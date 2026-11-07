from __future__ import annotations

import numpy as np
from sklearn.neighbors import NearestNeighbors

# scikit-learn rend 1 - cosinus : on remet le cosinus
def to_results(distances: np.ndarray, indices: np.ndarray) -> list[list[list]]:
    return [
        [[int(index), round(1 - float(distance), 3)] for index, distance in zip(row_indices, row_distances)]
        for row_indices, row_distances in zip(indices, distances)
    ]


# Pour chaque ligne de queries, ses k lignes les plus proches de catalogue
def search(queries: np.ndarray, catalogue: np.ndarray, k: int = 10) -> list[list[list]]:
    knn = NearestNeighbors(n_neighbors=min(k, len(catalogue)), metric="cosine").fit(catalogue)
    return to_results(*knn.kneighbors(queries))


# Pour chaque photo, ses k plus proches autres photos
def neighbors(embeddings: np.ndarray, k: int = 10) -> list[list[list]]:
    knn = NearestNeighbors(n_neighbors=min(k, len(embeddings) - 1), metric="cosine").fit(embeddings)
    return to_results(*knn.kneighbors())  # sans argument : exclut la photo elle-même


# top-k et mAP, sans les photos dont le dauphin n'a pas d'autre photo
def evaluate(embeddings: np.ndarray, individuals: np.ndarray) -> tuple[dict[str, float], int]:
    similarities = embeddings @ embeddings.T
    np.fill_diagonal(similarities, -np.inf)
    ranking = np.argsort(-similarities, axis=1)[:, :-1]

    is_correct = individuals[ranking] == individuals[:, None]
    counted = is_correct.any(axis=1)
    is_correct = is_correct[counted]

    first_correct_rank = is_correct.argmax(axis=1)
    scores = {f"top-{k}": round(float((first_correct_rank < k).mean()), 3) for k in (1, 5, 10)}

    precision = np.cumsum(is_correct, axis=1) / np.arange(1, is_correct.shape[1] + 1)
    scores["mAP"] = round(float(((precision * is_correct).sum(axis=1) / is_correct.sum(axis=1)).mean()), 3)
    return scores, int(counted.sum())


# Cosinus des paires même dauphin, puis dauphins différents
def pairs(embeddings: np.ndarray, individuals: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    each_pair = np.triu_indices(len(embeddings), k=1)
    cosines = (embeddings @ embeddings.T)[each_pair]
    same_individual = (individuals[:, None] == individuals[None, :])[each_pair]
    return cosines[same_individual], cosines[~same_individual]
