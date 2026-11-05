from __future__ import annotations

import csv
import hashlib
import re
import sys
import unicodedata
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
# D_TUTR0025_20111016_... : le côté, l'identifiant, puis la date sur 8 ou 6 chiffres
FILENAME = re.compile(r"^([DG])_+TUTR(\d{1,4})[_-]*(\d{8}|\d{6})?(?!\d)")
FOLDER = re.compile(r"^TUTR\d{4}$")  # TODO: trigger warning pour les noms


# 1. Les photos du dossier, sans les fichiers cachés
def find_photos(folder: str | Path) -> list[Path]:
    photos = []
    for path in sorted(Path(folder).rglob("*")):
        is_photo = path.is_file() and path.suffix.lower() in EXTENSIONS
        if is_photo and not path.name.startswith("."):
            photos.append(path)

    return photos


# Texte vers date, None si ce n'est pas une date
def parse_date(text: str, date_format: str) -> date | None:
    try:
        return datetime.strptime(text, date_format).date()
    except ValueError:
        return None


# 2. Le nom du fichier : côté, identifiant et date
def read_filename(name: str) -> tuple[str, str | None, date | None]:
    match = FILENAME.match(name)
    if not match:
        return "", None, None

    side, digits, text = match.groups()
    filename_date = None
    if text:
        filename_date = parse_date(text, "%Y%m%d" if len(text) == 8 else "%y%m%d")

    return side, f"TUTR{int(digits):04d}", filename_date


# 2. L'image : largeur, hauteur et date de prise de vue, None si elle est illisible
def read_image(path: Path) -> tuple[int | None, int | None, date | None]:
    try:
        with Image.open(path) as image:
            exif = image.getexif()
            text = exif.get_ifd(0x8769).get(36867) or exif.get(306) or ""  # DateTimeOriginal, sinon DateTime
            return image.width, image.height, parse_date(text.strip("\x00 "), "%Y:%m:%d %H:%M:%S")
    except (UnidentifiedImageError, OSError):
        return None, None, None


# 2. Le fichier : son empreinte unique
def sha256(path: Path) -> str:
    with open(path, "rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()


# 2 et 3. Une ligne du manifeste pour une photo
def describe_photo(path: Path) -> dict:
    # Le dossier donne le dauphin : c'est lui qui fait référence
    individual = path.parent.name
    if not FOLDER.match(individual):
        raise ValueError(f"Dossier de dauphin invalide : {individual}. Format attendu : TUTR0000/photo.jpg")

    # Les noms de fichiers sont écrits de la même façon sur Mac et sur Linux
    name = unicodedata.normalize("NFC", path.name)
    side, filename_id, filename_date = read_filename(name)
    width, height, exif_date = read_image(path)

    anomalies = []
    if filename_id is None:
        anomalies.append("nom illisible")
    elif filename_id != individual:
        anomalies.append(f"nom de fichier {filename_id} ≠ dossier {individual}")
    if filename_id and filename_date is None:
        anomalies.append("pas de date dans le nom")
    if width is None:
        anomalies.append("image illisible")
    if filename_date and exif_date and abs((filename_date - exif_date).days) > 1:
        anomalies.append("date du nom ≠ date EXIF")

    return {
        "fichier_origine": name,
        "individu": individual,
        "cote": side,
        "date_nom": filename_date,
        "date_exif": exif_date,
        "largeur": width,
        "hauteur": height,
        "sha256": sha256(path),
        "anomalies": " ; ".join(anomalies),
    }


# DATA QUALITY Doublons : même empreinte, donc même fichier TODO: IMPORTANT
def mark_duplicates(rows: list[dict]) -> None:
    counts = Counter(row["sha256"] for row in rows)
    for row in rows:
        if counts[row["sha256"]] > 1:
            row["anomalies"] = f"{row['anomalies']} ; doublon exact".removeprefix(" ; ")


# Le manifeste : une ligne par photo
def build_manifest(folder: str | Path) -> list[dict]:
    rows = [describe_photo(path) for path in find_photos(folder)]
    mark_duplicates(rows)

    return rows


# 4. L'écriture du CSV
def write_manifest(rows: list[dict], output: str | Path) -> None:
    with open(output, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    folder, output = sys.argv[1:3]
    rows = build_manifest(folder)
    write_manifest(rows, output)
    print(f"{len(rows)} photos : {output}")
