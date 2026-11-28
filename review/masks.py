"""Masques du dauphin (U-2-Net) pour `review.compare`.

Un masque par photo affichée (requête, bon dauphin, premiers faux candidats),
dans `data/derived/masques/`. Un masque existant est sauté.

    uv run --group ml python -m review.masks
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from review.compare import DATA, MODELS, mask_path, score_models

# CONSTANTES
MAX_SIDE = 512  # grand côté des masques enregistrés


def photos_to_mask(entries: list[dict], models) -> list[dict]:
    unique = {}
    for entry in entries:
        for photo in [entry["photo"], entry["bon"]] + [
            entry[model]["faux"] for model in models
        ]:
            unique.setdefault(photo["sha256"], photo)
    return list(unique.values())


def run(data: Path = DATA) -> None:
    from PIL import Image

    from dorsalmatch import Segmenter

    photos = photos_to_mask(score_models(data), MODELS)
    todo = [photo for photo in photos if not mask_path(data, photo).exists()]
    print(f"{len(photos)} photos, {len(todo)} masques à calculer", flush=True)
    if not todo:
        return
    segmenter = Segmenter()
    start = time.time()
    for number, photo in enumerate(todo, start=1):
        mask = segmenter.mask(photo["chemin"])
        mask.thumbnail((MAX_SIDE, MAX_SIDE), Image.NEAREST)
        path = mask_path(data, photo)
        path.parent.mkdir(parents=True, exist_ok=True)
        partial = path.with_suffix(".partiel.png")
        mask.save(partial)
        partial.replace(path)
        if number % 100 == 0 or number == len(todo):
            print(f"{number}/{len(todo)} en {time.time() - start:.0f} s", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data", type=Path, default=DATA)
    run(parser.parse_args().data)
