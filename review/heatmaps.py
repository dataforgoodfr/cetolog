"""Cartes Grad-CAM pour `review.compare`.

Pour chaque photo d'historique et chaque modèle : la requête contre le bon
dauphin, contre le premier faux candidat, et l'inverse. Les cartes vont dans
`data/derived/explications/gradcam/<modèle>/`. Une carte existante est sautée.
Les photos où les modèles ne sont pas d'accord passent en premier.

    uv run --group ml python -m review.heatmaps --model megadescriptor --limit 50
    uv run --group ml python -m review.heatmaps  # tous les modèles, toutes les photos
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np

from review.compare import DATA, MODELS, heatmap_path, score_models


# Désaccord d'abord : un modèle au rang 1 et un autre non, puis les échecs
def by_interest(entries: list[dict], models) -> list[dict]:
    def key(entry):
        rank1 = sum(entry[model]["rang"] == 1 for model in models)
        disagreement = 0 < rank1 < len(models)
        return (not disagreement, rank1)

    return sorted(entries, key=key)


# On garde les empreintes en mémoire, pas les tenseurs (plusieurs Go)
def run_model(model: str, entries: list[dict], data: Path = DATA) -> None:
    from PIL import Image

    from dorsalmatch import Embedder
    from dorsalmatch.explain import embed, grad_cam, to_tensor

    embedder = Embedder(model)
    embeddings = {}

    def tensor(photo):
        return to_tensor(embedder, Image.open(photo["chemin"]))

    def embedding(photo):
        key = photo["sha256"]
        if key not in embeddings:
            embeddings[key] = embed(embedder, tensor(photo))[0]
        return embeddings[key]

    start, done = time.time(), 0
    for number, entry in enumerate(entries, start=1):
        photo, match, false = entry["photo"], entry["bon"], entry[model]["faux"]
        for explained, reference in (
            (photo, match),
            (match, photo),
            (photo, false),
            (false, photo),
        ):
            path = heatmap_path(data, model, explained, reference)
            if path.exists():
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            heatmap = grad_cam(embedder, tensor(explained), embedding(reference))
            # Écrite puis renommée : pas de fichier tronqué si on arrête
            partial = path.with_suffix(".partiel.npy")
            np.save(partial, heatmap)
            partial.replace(path)
            done += 1
        if number % 10 == 0 or number == len(entries):
            print(
                f"{model} : {number}/{len(entries)} photos, {done} cartes "
                f"en {time.time() - start:.0f} s",
                flush=True,
            )


def run(models, limit: int | None, data: Path = DATA) -> None:
    entries = by_interest(score_models(data), MODELS)[:limit]
    for model in models:
        run_model(model, entries, data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model", choices=MODELS, action="append")
    parser.add_argument(
        "--limit", type=int, help="nombre de photos (désaccords d'abord)"
    )
    parser.add_argument("--data", type=Path, default=DATA)
    args = parser.parse_args()
    run(args.model or MODELS, args.limit, args.data)
