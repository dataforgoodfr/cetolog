from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from pipeline.photos.manifest import (
    add_anomaly,
    clean_name,
    find_photos,
    mark_duplicates,
    photo_row,
    process_all,
)

# CONSTANTES
DATA = Path("data")
KIND = "catalogue"
# DD_TUTR0001_img_8940.jpg
FILENAME = re.compile(r"^D([DG])_+([A-Z]{4})(\d{1,4})(?!\d)")


# Le nom du fichier : côté et identifiant
def read_filename(name: str) -> tuple[str, str | None]:
    match = FILENAME.match(name)
    if not match:
        return "", None

    side, letters, digits = match.groups()
    return side, f"{letters}{int(digits):04d}"


# Une ligne du manifeste pour une photo
def describe_photo(path: Path) -> dict:
    name = clean_name(path.name)
    side, individual = read_filename(name)

    anomalies = []
    if individual is None:
        anomalies.append("nom illisible")
        individual = "illisible"
    elif not individual.startswith("TUTR"):
        anomalies.append("identifiant hors TUTR")
    if name.lower().count(".jpg") > 1:
        anomalies.append("double extension")
    if path.suffix.lower() == ".png":
        anomalies.append("png")

    return photo_row(path, individual, side, None, anomalies)


# DATA QUALITY Une photo par dauphin et par côté
def mark_extra_photos(rows: list[dict]) -> None:
    counts = Counter((row["individu"], row["cote"]) for row in rows)
    for row in rows:
        if counts[(row["individu"], row["cote"])] > 1:
            add_anomaly(row, "plusieurs photos pour ce côté")


# Le manifeste : une ligne par photo
def build_manifest(folder: str | Path) -> list[dict]:
    rows = [describe_photo(path) for path in find_photos(folder)]
    mark_duplicates(rows)
    mark_extra_photos(rows)

    return rows


# python -m pipeline.photos.catalogue
def run(data: Path = DATA) -> None:
    process_all(KIND, build_manifest, data)


if __name__ == "__main__":
    run()
