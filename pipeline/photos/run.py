from __future__ import annotations

import shutil
import tempfile
import zipfile
from pathlib import Path

from pipeline.photos.manifest import build_manifest, find_photos, write_manifest

# CONSTANTES
DATA = Path("data")
ZIP_SUFFIX = "_photos.zip"


# Un zip devient des photos et un manifeste dans data/curated/
def process_zip(archive: Path, data: Path) -> None:
    delivery = archive.name.removesuffix(ZIP_SUFFIX)
    photos_folder = data / "curated" / "photos" / delivery
    manifest = data / "curated" / "manifests" / f"{delivery}.csv"

    # Déjà un manifeste : la livraison est finie
    if manifest.exists():
        print(f"{delivery} : déjà traitée")
        return

    with tempfile.TemporaryDirectory() as temporary:
        # Dézip
        with zipfile.ZipFile(archive) as content:
            content.extractall(temporary)

        # Manifeste
        rows = build_manifest(temporary)
        for row in rows:
            row["livraison"] = delivery

        # Photos
        for path, row in zip(find_photos(temporary), rows):  # les lignes sont dans l'ordre des photos
            destination = photos_folder / row["individu"] / row["fichier_origine"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)

    # En dernier : si le script s'arrête avant, il reprend au prochain lancement
    manifest.parent.mkdir(parents=True, exist_ok=True)
    write_manifest(rows, manifest)
    print(f"{delivery} : {len(rows)} photos, résultat dans {data / 'curated'}")


# Tous les zips de data/raw/photos/
def run(data: Path = DATA) -> None:
    archives = sorted((data / "raw" / "photos").glob("*.zip"))
    if not archives:
        print(f"Aucun zip dans {data / 'raw' / 'photos'}")

    for archive in archives:
        if archive.name.endswith(ZIP_SUFFIX):
            process_zip(archive, data)
        else:
            print(f"ignoré, nom attendu AAAA-MM-JJ_source{ZIP_SUFFIX} : {archive.name}")


if __name__ == "__main__":
    run()
