from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np

from demo.propositions import NEAR_IDENTICAL, SIDES, latest, load, rank

# CONSTANTES
DATA = Path("data")
COLUMNS = ["livraison", "individu", "cote", "fichier_origine", "rang", "score_premier", "score_bon", "score_premier_faux"]


# 1. Les photos de l'historique qu'on peut noter : leur côté est au catalogue, et ce n'est pas la même photo
def findable(photo, embedding, catalogue, catalogue_embeddings) -> bool:
    same = [line for line, other in enumerate(catalogue)
            if other["individu"] == photo["individu"] and other["cote"] == photo["cote"]]
    return photo["cote"] in SIDES and bool(same) and not (catalogue_embeddings[same] @ embedding >= NEAR_IDENTICAL).all()


# 2. Chaque photo cherchée dans le catalogue, comme dans la démo
# score_premier : ce que voit Miraceti pour un dauphin connu
# score_premier_faux : le meilleur score sans le bon dauphin, ce que verrait Miraceti s'il était nouveau
def score_photos(data: Path) -> list[dict]:
    catalogue, catalogue_embeddings = load("catalogue", latest("catalogue", data), data)

    rows = []
    for folder in sorted((data / "derived" / "embeddings" / "historique").iterdir()):
        photos, embeddings = load("historique", folder.name, data)
        for line, photo in enumerate(photos):
            if not findable(photo, embeddings[line], catalogue, catalogue_embeddings):
                continue
            candidates, _ = rank([photo], embeddings[[line]], catalogue, catalogue_embeddings)
            names = [candidate["individu"] for candidate in candidates]
            position = names.index(photo["individu"]) if photo["individu"] in names else None
            rows.append({
                "livraison": folder.name, "individu": photo["individu"], "cote": photo["cote"],
                "fichier_origine": photo["fichier_origine"],
                "rang": position + 1 if position is not None else "",
                "score_premier": candidates[0]["score"],
                "score_bon": candidates[position]["score"] if position is not None else "",
                "score_premier_faux": next(c["score"] for c in candidates if c["individu"] != photo["individu"]),
            })
    return rows


# 3. Top-1, top-5, top-10
def top_k(rows: list[dict]) -> dict[str, float]:
    ranks = np.array([row["rang"] or np.inf for row in rows], dtype=float)
    return {f"top-{k}": float((ranks <= k).mean()) for k in (1, 5, 10)}


# 4. Le seuil « probablement nouveau » : sous le seuil, le meilleur candidat ne ressemble pas assez
# Choisi pour équilibrer les dauphins connus gardés et les nouveaux repérés
def best_threshold(rows: list[dict]) -> tuple[float, float, float]:
    known = np.array([row["score_premier"] for row in rows])
    new = np.array([row["score_premier_faux"] for row in rows])
    thresholds = np.unique(np.concatenate([known, new]))
    kept = np.array([(known >= threshold).mean() for threshold in thresholds])
    flagged = np.array([(new < threshold).mean() for threshold in thresholds])
    best = int(np.argmax(kept + flagged))
    return float(thresholds[best]), float(kept[best]), float(flagged[best])


# 5. Les deux distributions et le seuil
def plot(rows: list[dict], output: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    known = [row["score_premier"] for row in rows]
    new = [row["score_premier_faux"] for row in rows]
    bins = np.linspace(min(new + known), max(new + known), 40)
    threshold, kept, flagged = best_threshold(rows)

    fig, ax = plt.subplots(figsize=(9, 3.6))
    ax.hist(known, bins=bins, alpha=0.6, color="#2e7d32", label="dauphin connu : score du premier candidat")
    ax.hist(new, bins=bins, alpha=0.6, color="#c62828", label="dauphin nouveau (simulé) : meilleur score sans lui")
    ax.axvline(threshold, color="black", linestyle="--",
               label=f"seuil {threshold:.2f} : {kept:.0%} des connus gardés, {flagged:.0%} des nouveaux repérés")
    ax.set_title(f"Scores sur l'historique · top-1 {top_k(rows)['top-1']:.0%}")
    ax.set_xlabel("score")
    ax.set_ylabel("photos")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(output, dpi=120)


# 6. Tout : les scores en CSV, le graphique, et le résumé à l'écran
def run(data: Path = DATA) -> Path:
    output = data / "derived" / "similarites" / latest("catalogue", data)
    output.mkdir(parents=True, exist_ok=True)

    rows = score_photos(data)
    with open(output / "scores.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    scores = top_k(rows)
    threshold, kept, flagged = best_threshold(rows)
    print(f"{len(rows)} photos · top-1 {scores['top-1']:.0%} · top-5 {scores['top-5']:.0%} · top-10 {scores['top-10']:.0%}")
    print(f"Seuil « nouveau » : {threshold:.2f} ({kept:.0%} des connus gardés, {flagged:.0%} des nouveaux repérés)")

    plot(rows, output / "distribution.png")
    return output


# uv run --group notebook python -m pipeline.similarities
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trace la distribution des scores sur l'historique, pour choisir un seuil.")
    parser.add_argument("--data", type=Path, default=DATA, help=f"dossier des données (défaut : {DATA})")
    print(f"Résultats : {run(parser.parse_args().data)}")
