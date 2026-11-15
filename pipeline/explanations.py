from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path

from PIL import Image

from pipeline.embeddings import read_photos

# CONSTANTES
DATA = Path("data")
KIND = "historique"  # des dauphins déjà identifiés : les paires sont connues
MODEL = "cetaceanet"
PAIRS = 25
COLUMNS = ["paire", "individu", "cote", "photo_a", "photo_b", "cosinus", "aire_carte", "aire_hasard", "image"]


# 1. Des paires connues : deux photos du même dauphin, du même côté
def known_pairs(photos: list[dict], count: int, seed: int = 0) -> list[tuple[dict, dict]]:
    groups = {}
    for photo in photos:
        if photo["cote"] in ("D", "G"):
            groups.setdefault((photo["individu"], photo["cote"]), []).append(photo)

    rng = random.Random(seed)
    keys = sorted(key for key, group in groups.items() if len(group) >= 2)
    return [tuple(rng.sample(groups[key], 2)) for key in rng.sample(keys, min(count, len(keys)))]


# 2. Chaque paire expliquée : une image à revoir avec l'équipe, une ligne du résumé
def run(count: int = PAIRS, method: str = "occlusion", data: Path = DATA) -> Path:
    from dorsalmatch import Embedder
    from dorsalmatch.explain import explain, side_by_side

    manifest = max((data / "curated" / KIND / "manifests").glob("*.csv"))
    output = data / "derived" / "explications" / KIND / manifest.stem / method
    output.mkdir(parents=True, exist_ok=True)
    embedder = Embedder(MODEL)

    rows = []
    pairs = known_pairs(read_photos(manifest, KIND, data), count)
    for number, (a, b) in enumerate(pairs, start=1):
        print(f"{number}/{len(pairs)} : {a['individu']} côté {a['cote']}", flush=True)
        result = explain(embedder, Image.open(a["chemin"]), Image.open(b["chemin"]), method)
        image = f"{number:02d}_{a['individu']}_{a['cote']}.jpg"
        side_by_side([result["requete"], result["candidat"], result["liens"]]).save(output / image)
        rows.append({"paire": number, "individu": a["individu"], "cote": a["cote"],
                     "photo_a": a["fichier_origine"], "photo_b": b["fichier_origine"],
                     "cosinus": round(result["cosinus"], 3), "aire_carte": round(result["aire_carte"], 3),
                     "aire_hasard": round(result["aire_hasard"], 3), "image": image})

    summary = output / "resume.csv"
    with open(summary, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return summary


# uv run --group ml python -m pipeline.explanations
# uv run --group ml python -m pipeline.explanations --pairs 30 --method gradcam
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Explique des paires connues de l'historique, pour une revue en équipe.")
    parser.add_argument("--pairs", type=int, default=PAIRS, help=f"nombre de paires (défaut : {PAIRS})")
    parser.add_argument("--method", choices=("occlusion", "gradcam"), default="occlusion")
    parser.add_argument("--data", type=Path, default=DATA, help=f"dossier des données (défaut : {DATA})")
    args = parser.parse_args()
    print(f"Résumé : {run(args.pairs, args.method, args.data)}")
