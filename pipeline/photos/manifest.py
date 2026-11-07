from __future__ import annotations

import csv
import hashlib
import shutil
import tempfile
import unicodedata
import zipfile
from collections import Counter
from datetime import date, datetime
from pathlib import Path

from PIL import Image, UnidentifiedImageError

# CONSTANTES
EXTENSIONS = {".jpg", ".jpeg", ".png"}
COLUMNS = [
    "livraison", "fichier_origine", "individu",
    "cote", "date_nom", "date_exif", "largeur",
    "hauteur", "sha256", "anomalies",
]


# Les photos du dossier, sans les fichiers cachés
def find_photos(folder: str | Path) -> list[Path]:
    photos = []
    for path in sorted(Path(folder).rglob("*")):
        is_photo = path.is_file() and path.suffix.lower() in EXTENSIONS
        if is_photo and not path.name.startswith("."):
            photos.append(path)

    return photos


# Même nom sur Mac et Linux
def clean_name(name: str) -> str:
    return unicodedata.normalize("NFC", name)


# Texte vers date, None si ce n'est pas une date
def parse_date(text: str, date_format: str) -> date | None:
    try:
        return datetime.strptime(text, date_format).date()
    except ValueError:
        return None


# Largeur, hauteur et date EXIF, None si illisible
def read_image(path: Path) -> tuple[int | None, int | None, date | None]:
    try:
        with Image.open(path) as image:
            exif = image.getexif()
            text = exif.get_ifd(0x8769).get(36867) or exif.get(306) or ""  # DateTimeOriginal, sinon DateTime
            return image.width, image.height, parse_date(text.strip("\x00 "), "%Y:%m:%d %H:%M:%S")
    except (UnidentifiedImageError, OSError):
        return None, None, None


# Le fichier : son empreinte unique
def sha256(path: Path) -> str:
    with open(path, "rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()


# Une ligne du manifeste
def photo_row(path: Path, individual: str, side: str, filename_date: date | None, anomalies: list[str]) -> dict:
    width, height, exif_date = read_image(path)

    if width is None:
        anomalies.append("image illisible")
    if filename_date and exif_date and abs((filename_date - exif_date).days) > 1:
        anomalies.append("date du nom ≠ date EXIF")

    return {
        "fichier_origine": clean_name(path.name),
        "individu": individual,
        "cote": side,
        "date_nom": filename_date,
        "date_exif": exif_date,
        "largeur": width,
        "hauteur": height,
        "sha256": sha256(path),
        "anomalies": " ; ".join(anomalies),
        "chemin": path,
    }


# Ajoute une anomalie à une ligne
def add_anomaly(row: dict, anomaly: str) -> None:
    row["anomalies"] = f"{row['anomalies']} ; {anomaly}".removeprefix(" ; ")


# DATA QUALITY Doublons
def mark_duplicates(rows: list[dict]) -> None:
    counts = Counter(row["sha256"] for row in rows)
    for row in rows:
        if counts[row["sha256"]] > 1:
            add_anomaly(row, "doublon exact")


# L'écriture du CSV
def write_manifest(rows: list[dict], output: str | Path) -> None:
    with open(output, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


# Un zip de raw/ -> photos et manifeste dans curated/
def process_zip(archive: Path, kind: str, build_manifest, data: Path) -> None:
    delivery = archive.stem
    photos_folder = data / "curated" / kind / "photos" / delivery
    manifest = data / "curated" / kind / "manifests" / f"{delivery}.csv"

    # Déjà un manifeste : la livraison est finie
    if manifest.exists():
        print(f"{delivery} : déjà traitée")
        return

    with tempfile.TemporaryDirectory() as temporary:
        # 1. Dézip
        with zipfile.ZipFile(archive) as content:
            content.extractall(temporary)

        # 2. Manifeste
        rows = build_manifest(temporary)
        for row in rows:
            row["livraison"] = delivery

        # 3. Photos rangées par individu
        for row in rows:
            destination = photos_folder / row["individu"] / row["fichier_origine"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(row["chemin"], destination)

    # 4. Manifeste en dernier : un arrêt reprend au prochain lancement
    manifest.parent.mkdir(parents=True, exist_ok=True)
    write_manifest(rows, manifest)
    print(f"{delivery} : {len(rows)} photos, résultat dans {photos_folder}")


# Tous les zips de data/raw/<type>/
def process_all(kind: str, build_manifest, data: Path) -> None:
    archives = sorted((data / "raw" / kind).glob("*.zip"))
    if not archives:
        print(f"Aucun zip dans {data / 'raw' / kind}")

    for archive in archives:
        process_zip(archive, kind, build_manifest, data)
