import hashlib
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from PIL import Image
from sqlalchemy import create_engine

load_dotenv()

# Chemins utilisés : le dossier du catalogue et la destination des CSV
# (à lancer depuis backend/)

base_dir = Path.cwd().parent
livraison = "catalogue_20261029_miraceti"
chemin_catalogue = base_dir / "data" / livraison
chemin_destination = base_dir / "data" / "seed"


# Création des empreintes fichiers sha256


def calculer_hash(image_path):
    sha256 = hashlib.sha256()

    with open(image_path, "rb") as f:
        for bloc in iter(lambda: f.read(4096), b""):
            sha256.update(bloc)

    return sha256.hexdigest()


photos_catalogue = sorted(
    f for f in chemin_catalogue.iterdir() if f.is_file() and not f.name.startswith(".")
)

dates_exif = {}
hashcodes = {}

for photo in photos_catalogue:
    # Récupération de la date de prise de vue EXIF (DateTimeOriginal)
    exif = Image.open(photo).getexif().get_ifd(0x8769)
    dates_exif[photo.name] = exif.get(36867)

    # Calcul du hashcode
    hashcodes[photo.name] = calculer_hash(photo)


df_photos = pd.DataFrame(
    {"date_exif": pd.Series(dates_exif), "sha256": pd.Series(hashcodes)}
)

print(df_photos.shape)


# Lecture du nom : <Côté>_<Individu>_<AAAAMMJJ>_<Site>_<libre>.jpg

df_photos["delivery"] = livraison
df_photos["original_filename"] = df_photos.index.astype(str)

blocs = df_photos["original_filename"].str.rsplit(".", n=1).str[0].str.split("_")

df_photos["side"] = blocs.str[0].where(blocs.str[0].isin(["D", "G"]))
df_photos["individual"] = blocs.str[1].where(
    blocs.str[1].str.fullmatch(r"TUTR\d{4}", na=False)
)

date_nom = pd.to_datetime(blocs.str[2], format="%Y%m%d", errors="coerce")
date_exif = pd.to_datetime(
    df_photos["date_exif"], format="%Y:%m:%d %H:%M:%S", errors="coerce"
)

# La date du nom, à défaut celle de l'EXIF (data contract)
df_photos["date"] = date_nom.fillna(date_exif).dt.date

# Le site n'est lu que si la date du nom est à sa place et suivie du libre
df_photos["site"] = blocs.str[3].where(date_nom.notna() & (blocs.str.len() > 4))


# Les deux tables : individuals et photos

df_individuals = (
    df_photos[["individual"]]
    .dropna()
    .drop_duplicates()
    .rename(columns={"individual": "code"})
    .sort_values("code")
)

df_photos = df_photos[
    [
        "delivery",
        "original_filename",
        "individual",
        "side",
        "date",
        "site",
        "sha256",
    ]
].reset_index(drop=True)

print(f"photos : {len(df_photos)} | individus : {len(df_individuals)}")
print(df_photos.isna().sum().to_string())


# Écriture des CSV, pour relire avant la mise en base

chemin_destination.mkdir(parents=True, exist_ok=True)
df_individuals.to_csv(chemin_destination / "individuals.csv", index=False)
df_photos.to_csv(chemin_destination / "photos.csv", index=False)

print(f"fichiers .csv créés dans {chemin_destination}")


# Mise en base : les individus, puis les photos reliées à leur individu

engine = create_engine(os.environ["DATABASE_URL"])

with engine.begin() as conn:
    deja_charge = pd.read_sql(
        "SELECT count(*) AS n FROM photos WHERE delivery = %(livraison)s",
        conn,
        params={"livraison": livraison},
    )["n"][0]

    if deja_charge:
        raise SystemExit(f"{livraison} est déjà en base ({deja_charge} photos)")

    connus = pd.read_sql("SELECT code FROM individuals", conn)["code"]
    nouveaux = df_individuals[~df_individuals["code"].isin(connus)]
    nouveaux.to_sql("individuals", conn, if_exists="append", index=False)

    ids = pd.read_sql("SELECT id AS individual_id, code FROM individuals", conn)
    df_final = df_photos.merge(
        ids, left_on="individual", right_on="code", how="left"
    ).drop(columns=["individual", "code"])
    df_final.to_sql("photos", conn, if_exists="append", index=False)

print(f"individus ajoutés : {len(nouveaux)} | photos ajoutées : {len(df_final)}")
