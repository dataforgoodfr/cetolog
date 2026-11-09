from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

import dorsalmatch

# CONSTANTES
DATA = Path("data")
TOP = 10
COLUMNS = ["best_of", "catalogue", "individu", "rang", "candidat", "score", "cosinus_D", "cosinus_G", "deja_au_catalogue"]
MODEL = "cetaceanet_v2"
SIDES = ("D", "G")
# Au-delà, même photo déjà au catalogue : écartée, mais donne la réponse
NEAR_IDENTICAL = 0.97


# Les photos d'une livraison et leurs empreintes
def load(kind: str, delivery: str, data: Path = DATA) -> tuple[list[dict], np.ndarray]:
    folder = data / "derived" / "embeddings" / kind / delivery
    # keep_default_na=False : un côté vide reste "", pas NaN
    photos = pd.read_csv(folder / "photos.csv", dtype=str, keep_default_na=False)
    photos["chemin"] = [str(data / "curated" / kind / "photos" / delivery / individual / name)
                        for individual, name in zip(photos["individu"], photos["fichier_origine"])]
    return photos.to_dict("records"), np.load(folder / f"{MODEL}.npy")


# La dernière livraison d'un type
def latest(kind: str, data: Path = DATA) -> str:
    return max(folder.name for folder in (data / "derived" / "embeddings" / kind).iterdir() if folder.is_dir())


# IND2 avant IND10
def by_number(name: str) -> int:
    return int(re.sub(r"\D", "", name) or 0)


# 1. Toutes les photos de l'individu contre un côté du catalogue : le meilleur cosinus de chaque dauphin
def best_cosines(photos, embeddings, catalogue, catalogue_embeddings, side: str) -> tuple[dict[str, float], set[str]]:
    lines = [line for line, photo in enumerate(photos) if photo["cote"] in SIDES]
    catalogue_lines = [line for line, photo in enumerate(catalogue) if photo["cote"] == side]
    if not lines or not catalogue_lines:
        return {}, set()

    best, identical = {}, set()
    results = dorsalmatch.search(embeddings[lines], catalogue_embeddings[catalogue_lines], k=len(catalogue_lines))
    for closest in results:
        for position, cosine in closest:
            individual = catalogue[catalogue_lines[position]]["individu"]
            if cosine >= NEAR_IDENTICAL:
                identical.add(individual)
                continue
            best[individual] = max(best.get(individual, -1.0), cosine)
    return best, identical


# 2. Score : le meilleur cosinus, tous côtés confondus
def rank(photos, embeddings, catalogue, catalogue_embeddings) -> tuple[list[dict], set[str]]:
    by_side, identical = {}, set()
    for side in SIDES:
        by_side[side], found = best_cosines(photos, embeddings, catalogue, catalogue_embeddings, side)
        identical |= found

    candidates = []
    for individual in set(by_side["D"]) | set(by_side["G"]):
        scores = {side: by_side[side][individual] for side in SIDES if individual in by_side[side]}
        candidates.append({"individu": individual, "score": float(max(scores.values())), **scores})

    # À score égal, par identifiant : le classement ne change pas d'un lancement à l'autre
    return sorted(candidates, key=lambda candidate: (-candidate["score"], candidate["individu"])), identical


# 3. Les candidats de chaque individu d'un best-of
def propose(best_of: str, catalogue_delivery: str, data: Path = DATA) -> dict[str, dict]:
    photos, embeddings = load("best_of", best_of, data)
    catalogue, catalogue_embeddings = load("catalogue", catalogue_delivery, data)

    propositions = {}
    for individual in sorted({photo["individu"] for photo in photos}, key=by_number):
        lines = [line for line, photo in enumerate(photos) if photo["individu"] == individual]
        mine = [photos[line] for line in lines]
        candidates, identical = rank(mine, embeddings[lines], catalogue, catalogue_embeddings)
        propositions[individual] = {"photos": mine, "candidats": candidates, "reponse": sorted(identical)}
    return propositions


# (dauphin, côté) -> photo du catalogue
def catalogue_photos(catalogue: list[dict]) -> dict[tuple[str, str], str]:
    photos = {}
    for photo in catalogue:
        photos.setdefault((photo["individu"], photo["cote"]), photo["chemin"])
    return photos


# 4. Les TOP candidats dans derived/propositions/<best_of>.csv
def write(best_of: str, catalogue_delivery: str, data: Path = DATA) -> Path:
    rows = []
    for individual, proposition in propose(best_of, catalogue_delivery, data).items():
        for rank, candidate in enumerate(proposition["candidats"][:TOP], start=1):
            rows.append({
                "best_of": best_of, "catalogue": catalogue_delivery, "individu": individual, "rang": rank,
                "candidat": candidate["individu"], "score": round(candidate["score"], 3),
                "cosinus_D": round(candidate["D"], 3) if "D" in candidate else "",
                "cosinus_G": round(candidate["G"], 3) if "G" in candidate else "",
                "deja_au_catalogue": " ; ".join(proposition["reponse"]),
            })

    output = data / "derived" / "propositions" / f"{best_of}.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=COLUMNS).to_csv(output, index=False, encoding="utf-8")
    return output
