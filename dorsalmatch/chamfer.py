import numpy as np

MODES = ("max", "chamfer_asym", "chamfer_sym")  # par défaut max()
SIDES = ("D", "G")
# Au-delà, même photo déjà au catalogue : écartée, mais donne la réponse
NEAR_IDENTICAL = 0.97


# Similarités cosinus arrondies
def cosine_similarity_matrix(queries, candidates, near_identical):
    q, c = np.asarray(queries, float), np.asarray(candidates, float)
    if q.ndim != 2 or c.ndim != 2 or q.shape[1] != c.shape[1]:
        raise ValueError("matrices 2D de même dimension attendues")
    q = q / np.maximum(np.linalg.norm(q, axis=1, keepdims=True), 1e-12)
    c = c / np.maximum(np.linalg.norm(c, axis=1, keepdims=True), 1e-12)
    sim = np.round(q @ c.T, 3)
    if near_identical is not None:
        sim[sim >= near_identical] = -np.inf  # quasi-doublons sont masqués
    return sim


# Moyenne des meilleurs cosinus par ligne
def _mean_best(sim):
    best = sim.max(axis=1, initial=-np.inf)
    best = best[np.isfinite(best)]
    return best.mean() if best.size else None


# Score de deux ensembles d'embeddings
def score(queries, candidates, mode="max", near_identical=0.97):
    sim = cosine_similarity_matrix(queries, candidates, near_identical)
    if not np.isfinite(sim).any():
        return None
    if mode == "max":
        return float(sim.max())
    forward = _mean_best(sim)
    if mode == "chamfer_asym":
        return None if forward is None else float(forward)
    backward = _mean_best(sim.T)
    values = [v for v in (forward, backward) if v is not None]
    return float(np.mean(values)) if values else None


# Toutes les photos de l'individu contre un côté du catalogue.
# Le meilleur cosinus de chaque dauphin, sans k-NN
def best_cosines(
    photos, embeddings, catalogue, catalogue_embeddings, side: str, mode="max"
) -> tuple[dict[str, float], set[str]]:
    lines = [line for line, photo in enumerate(photos) if photo["cote"] in SIDES]
    catalogue_lines = [
        line for line, photo in enumerate(catalogue) if photo["cote"] == side
    ]
    if not lines or not catalogue_lines:
        return {}, set()

    q = embeddings[lines]
    g = catalogue_embeddings[catalogue_lines]
    names = np.array([catalogue[i]["individu"] for i in catalogue_lines])
    raw = cosine_similarity_matrix(q, g, near_identical=None)

    best, identical = {}, set()
    for name in np.unique(names):
        cols = names == name
        if (raw[:, cols] >= NEAR_IDENTICAL).any():
            identical.add(str(name))
        value = score(q, g[cols], mode=mode, near_identical=NEAR_IDENTICAL)
        if value is not None:
            best[str(name)] = value
    return best, identical


# Score : le meilleur cosinus, tous côtés confondus
def rank(
    photos, embeddings, catalogue, catalogue_embeddings, mode="max"
) -> tuple[list[dict], set[str]]:
    by_side, identical = {}, set()
    for side in SIDES:
        by_side[side], found = best_cosines(
            photos, embeddings, catalogue, catalogue_embeddings, side, mode
        )
        identical |= found

    candidates = []
    for individual in set(by_side["D"]) | set(by_side["G"]):
        scores = {
            side: by_side[side][individual]
            for side in SIDES
            if individual in by_side[side]
        }
        candidates.append(
            {"individu": individual, "score": float(max(scores.values())), **scores}
        )

    # À score égal, par identifiant.
    # Le classement ne change pas d'un lancement à l'autre.
    return sorted(
        candidates, key=lambda candidate: (-candidate["score"], candidate["individu"])
    ), identical
