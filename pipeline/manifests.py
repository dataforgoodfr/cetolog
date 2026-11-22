import hashlib
import os
import zipfile
from pathlib import Path

import pandas as pd
from PIL import Image
from PIL.ExifTags import TAGS

# Chemins utilisés pour récupération des ZIP et destination des photos

base_dir = Path.cwd().parent
chemin_zip_raw = base_dir / "data" / "raw" / "catalogue"
chemin_destination = base_dir / "data" / "test"
fichiers_source = chemin_zip_raw.rglob("*.zip")

for fichier_source in fichiers_source:
    with zipfile.ZipFile(fichier_source, "r") as zip_ref:
        zip_ref.extractall(chemin_destination)

    print("catalogue décompressé avec succès !")


# Création des empreintes fichiers sha256


def calculer_hash(image_path):
    sha256 = hashlib.sha256()

    with open(image_path, "rb") as f:
        for bloc in iter(lambda: f.read(4096), b""):
            sha256.update(bloc)

    return sha256.hexdigest()


photos_test = [
    f
    for f in chemin_destination.rglob("*")
    if f.suffix.lower() in {".jpg", ".jpeg", ".png"}
]

resultats = {}
hashcodes = {}

for photo in photos_test:
    # Récupération des métadonnées EXIF
    img = Image.open(photo)
    exif_data = img._getexif()

    if exif_data:
        resultats[photo.name] = {
            TAGS.get(tag_id, tag_id): value for tag_id, value in exif_data.items()
        }

    # Calcul du hashcode
    hashcodes[photo.name] = calculer_hash(photo)


df_resultats = pd.DataFrame.from_dict(resultats, orient="index")
df_hashcodes = pd.DataFrame.from_dict(hashcodes, orient="index")

print(df_resultats.shape)
print(df_hashcodes.shape)


df_merge = pd.merge(
    df_resultats, df_hashcodes, left_index=True, right_index=True, how="right"
)


df_merge = df_merge.rename(columns={0: "sha_256"})
df_merge["livraison"] = fichier_source.stem
df_merge["fichier_origine"] = df_merge.index.astype(str)
df_merge["cote"] = df_merge["fichier_origine"].str[1]
df_merge["individu"] = df_merge["fichier_origine"].str[3:11]

df_final = df_merge[
    ["livraison", "fichier_origine", "individu", "cote", "DateTimeOriginal", "sha_256"]
]

df_final = df_final.rename(columns={"DateTimeOriginal": "date"})

df_final["date"] = pd.to_datetime(
    df_final["date"], format="%Y:%m:%d %H:%M:%S", errors="coerce"
).dt.strftime("%Y-%m-%d")


def detecter_anomalies(row):
    anomalies = []

    if df_final["sha_256"].duplicated(keep=False).loc[row.name]:
        anomalies.append("Doublon SHA256")

    extension = os.path.splitext(str(row["fichier_origine"]))[1]

    if extension.lower() != ".jpg":
        anomalies.append(f"Extension incorrecte ({extension})")

    return " ; ".join(anomalies) if anomalies else ""


df_final["anomalies"] = df_final.apply(detecter_anomalies, axis=1)


df_final.to_csv("test_manifests.csv", index=False)

print("fichier .csv créé")
