from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np

# CONSTANTES
DATA = Path("data")
KINDS = ("catalogue", "best_of")
MODELS = ["cetaceanet"]
COLUMNS = ["livraison", "individu", "cote", "fichier_origine", "sha256"]


# 1. Les photos du manifeste présentes dans curated/
def read_photos(manifest: Path, kind: str, data: Path) -> list[dict]:
    with open(manifest, encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    photos_folder = data / "curated" / kind / "photos" / manifest.stem
    kept = []
    for row in rows:
        path = photos_folder / row["individu"] / row["fichier_origine"]
        if path.exists():
            kept.append({**row, "chemin": path})
        else:
            print(f"  photo manquante, ignorée : {path}")

    return kept


# 2. Les empreintes d'une livraison
def embed_delivery(embedder, model: str, manifest: Path, kind: str, data: Path) -> None:
    output = data / "derived" / "embeddings" / kind / manifest.stem
    embeddings_file = output / f"{model}.npy"
    if embeddings_file.exists():
        print(f"{kind}/{manifest.stem} : {model} déjà calculé")
        return

    rows = read_photos(manifest, kind, data)
    print(f"{kind}/{manifest.stem} : {len(rows)} photos avec {model}", flush=True)
    embeddings = embedder.embed([row["chemin"] for row in rows])

    # Empreintes en dernier : un calcul coupé est refait
    output.mkdir(parents=True, exist_ok=True)
    with open(output / "photos.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    np.save(embeddings_file, embeddings)


# 3. Toutes les livraisons, modèle par modèle
def run(models: list[str] = MODELS, data: Path = DATA, kinds: tuple[str, ...] = KINDS) -> None:
    from dorsalmatch import Embedder

    for model in models:
        embedder = Embedder(model)
        for kind in kinds:
            for manifest in sorted((data / "curated" / kind / "manifests").glob("*.csv")):
                embed_delivery(embedder, model, manifest, kind, data)


# uv run --group ml python -m pipeline.embeddings
if __name__ == "__main__":
    run(sys.argv[1:] or MODELS)
