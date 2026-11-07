from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from pipeline.photos.manifest import (
    clean_name,
    find_photos,
    mark_duplicates,
    parse_date,
    photo_row,
    process_all,
)


# CONSTANTES
DATA = Path("data")
KIND = "best_of"
# D_3_20230307_Sete_...
FILENAME = re.compile(r"^([DG])_(\d+)_(\d{8})?")
FOLDER = re.compile(r"^IND(\d+)$")


# Le nom du fichier : côté, numéro de l'individu et date
def read_filename(name: str) -> tuple[str, str | None, date | None]:
    match = FILENAME.match(name)
    if not match:
        return "", None, None

    side, number, text = match.groups()
    filename_date = parse_date(text, "%Y%m%d") if text else None

    return side, number, filename_date


# Une ligne du manifeste pour une photo
def describe_photo(path: Path) -> dict:
    # Le dossier fait référence
    individual = path.parent.name
    folder_number = FOLDER.match(individual).group(1)

    side, filename_number, filename_date = read_filename(clean_name(path.name))

    anomalies = []
    if filename_number is None:
        anomalies.append("nom illisible")
    elif int(filename_number) != int(folder_number):
        anomalies.append(f"nom de fichier {filename_number} ≠ dossier {individual}")
    if filename_number and filename_date is None:
        anomalies.append("pas de date dans le nom")

    return photo_row(path, individual, side, filename_date, anomalies)


# Le manifeste : une ligne par photo des dossiers IND, le reste est ignoré
def build_manifest(folder: str | Path) -> list[dict]:
    rows = []
    for path in find_photos(folder):
        if FOLDER.match(path.parent.name):
            rows.append(describe_photo(path))
    mark_duplicates(rows)

    return rows


# python -m pipeline.photos.best_of
def run(data: Path = DATA) -> None:
    process_all(KIND, build_manifest, data)


if __name__ == "__main__":
    run()
