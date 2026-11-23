"""Scoring et classification des résultats de classement pour les photos
d'historique.

Chaque photo trouvable est classée avec `demo.propositions.rank`, puis
analysée pour déterminer si le vrai dauphin est bien classé (position 1),
mal classé dans le top, ou hors du top. Une photo déjà présente au
catalogue (score >= 0.97 sur toutes les photos du même dauphin et du même
côté) est écartée, de même qu'une photo dont le côté manque au catalogue.

Le module est consommé par `review.app` pour construire l'interface FiftyOne
de review qualitative.
"""

from __future__ import annotations

from collections.abc import Sequence
from enum import StrEnum
from pathlib import Path
from typing import NamedTuple

import numpy as np

from demo.propositions import DATA, TOP, load, rank
from pipeline.similarities import findable

# Les deux livraisons notées dans le notebook, puis le catalogue.
HISTORY_DELIVERIES = (
    "2026-10-29_miraceti",
    "2026-11-06_bestof_20230307_sete",
)
CATALOGUE_DELIVERY = "2026-11-06_catalogue_tt"


class RankingOutcome(StrEnum):
    """Classification du résultat du classement.

    Trois catégories possibles : bien rangé (position 1), mal rangé dans
    le top (positions 2 à TOP), ou hors du top (position > TOP ou absent
    du classement).
    """

    WELL_RANKED = "bien rangé"
    TOP_MISRANKED = f"top {TOP}, mal rangé"
    OUTSIDE_TOP = f"hors top {TOP}"


class RankingResult(NamedTuple):
    """Une photo de l'historique notée.

    Attributes
    ----------
    ranking_outcome : RankingOutcome
        Classification of the ranking result.
    match_rank : int or None
        Place du bon dauphin dans le classement ML, à partir de 1. `None`
        s'il est absent. C'est un rang du dauphin, indépendant du côté : si
        un dauphin a deux photos (D et G), toutes deux auront le même
        `match_rank` pour une requête donnée.
    side : str
        Côté de la photo d'historique, `D` ou `G`.
    delivery : str
        Livraison d'historique d'où vient la photo.
    individual : str
        Dauphin annoté sur la photo d'historique.
    match_score : float or None
        Score du bon dauphin. `None` s'il est absent du classement.
    first_false_score : float or None
        Score du meilleur dauphin qui n'est pas le bon.
    filepath : str
        Photo d'historique, sous `data/curated/`.
    candidate_photos : list[dict]
        Les 10 premiers candidats de `rank`, avec leur score. Dans
        `review/app.py`, ces photos sont copiées en photos affichées avec
        une `position` (distinct de `match_rank`) : deux photos du même
        dauphin de côtés différents peuvent avoir des positions différentes.
    """

    ranking_outcome: RankingOutcome
    match_rank: int | None
    side: str
    delivery: str
    individual: str
    match_score: float | None
    first_false_score: float | None
    filepath: str
    candidate_photos: list[dict]


def ranking_outcome(match_rank: int | None) -> RankingOutcome:
    """Détermine le résultat du classement selon la position obtenue.

    Classifie le résultat en trois catégories : bien classé (position 1),
    mal classé dans le top (positions 2 à TOP), ou hors du top (position
    > TOP ou absent du classement).

    Parameters
    ----------
    match_rank : int or None
        Place du meilleur appariement, à partir de 1. `None` s'il est
        absent du classement.

    Returns
    -------
    RankingOutcome
        Un des trois résultats de classement possibles.
    """
    if match_rank == 1:
        return RankingOutcome.WELL_RANKED
    if match_rank is not None and match_rank <= TOP:
        return RankingOutcome.TOP_MISRANKED
    return RankingOutcome.OUTSIDE_TOP


def _load_history(
    data: Path, deliveries: Sequence[str]
) -> tuple[list[dict[str, str]], np.ndarray]:
    """Empile les photos et les empreintes de plusieurs livraisons.

    Parameters
    ----------
    data : Path
        Racine des données, avec `derived/` et `curated/`.
    deliveries : Sequence[str]
        Noms des livraisons d'historique, dans l'ordre voulu.

    Returns
    -------
    tuple[list[dict[str, str]], np.ndarray]
        Photos avec leur livraison d'origine, puis les empreintes
        dans le même ordre.
    """
    photos: list[dict[str, str]] = []
    embeddings = []
    for delivery in deliveries:
        delivery_photos, delivery_embeddings = load("historique", delivery, data)
        photos += [{**photo, "livraison": delivery} for photo in delivery_photos]
        embeddings.append(delivery_embeddings)
    return photos, np.vstack(embeddings)


def score_historical_photos(
    data: Path = DATA,
    history_deliveries: Sequence[str] = HISTORY_DELIVERIES,
    catalogue_delivery: str = CATALOGUE_DELIVERY,
) -> tuple[list[RankingResult], np.ndarray]:
    """Note chaque photo d'historique que le catalogue permet de juger.

    Parameters
    ----------
    data : Path
        Racine des données, avec `derived/` et `curated/`.
    history_deliveries : Sequence[str]
        Livraisons d'historique. Par défaut, celles du notebook.
    catalogue_delivery : str
        Livraison du catalogue. Par défaut, celle du notebook.

    Returns
    -------
    tuple[list[RankingResult], np.ndarray]
        Une entrée par photo d'historique classée, dans l'ordre des
        livraisons, puis les empreintes CetaceaNet de ces photos, même
        ordre. Le classement de chaque entrée est celui de `rank`.
    """
    history, embeddings = _load_history(data, history_deliveries)
    catalogue, catalogue_embeddings = load("catalogue", catalogue_delivery, data)

    ranking_results: list[RankingResult] = []
    kept: list[np.ndarray] = []
    for line, photo in enumerate(history):
        if not findable(photo, embeddings[line], catalogue, catalogue_embeddings):
            continue
        candidate_photos, _ = rank(
            [photo],
            embeddings[line : line + 1],
            catalogue,
            catalogue_embeddings,
        )
        individual = photo["individu"]
        candidate_individuals = [
            candidate_photo["individu"] for candidate_photo in candidate_photos
        ]
        match_index = (
            candidate_individuals.index(individual)
            if individual in candidate_individuals
            else None
        )
        match_rank = match_index + 1 if match_index is not None else None
        match_score = (
            float(candidate_photos[match_index]["score"])
            if match_index is not None
            else None
        )
        first_false_score = next(
            (
                float(candidate_photo["score"])
                for candidate_photo in candidate_photos
                if candidate_photo["individu"] != individual
            ),
            None,
        )
        ranking_results.append(
            RankingResult(
                ranking_outcome=ranking_outcome(match_rank),
                match_rank=match_rank,
                side=photo["cote"],
                delivery=photo["livraison"],
                individual=photo["individu"],
                match_score=match_score,
                first_false_score=first_false_score,
                filepath=photo["chemin"],
                candidate_photos=candidate_photos[:TOP],
            )
        )
        kept.append(embeddings[line])
    if not kept:
        return ranking_results, np.empty((0, embeddings.shape[1]))
    return ranking_results, np.stack(kept)
