"""Revue locale des photos d'historique dans FiftyOne.

Les photos restent des chemins vers `data/curated/`. L'index FiftyOne
reste dans `~/.fiftyone`, pas dans le dépôt, et rien n'est envoyé.

Concepts clés:
- `match_rank` : place du dauphin annoté dans le classement du ML (à partir
  de 1). C'est une propriété du dauphin, indépendante du côté. Si un dauphin
  a deux photos (droite et gauche) au catalogue, les deux portent le même
  `match_rank` pour une requête donnée.
- `position` : place d'une photo dans le groupe affichage (à partir de 0 pour
  la requête). Contrairement à `match_rank`, deux photos du même dauphin mais
  de côtés différents peuvent avoir des positions différentes, triées par
  score du côté affiché.
"""

from __future__ import annotations

import os
from collections.abc import Sequence
from pathlib import Path
from typing import NamedTuple

import numpy as np

from demo.propositions import SIDES
from review.ranking import (
    CATALOGUE_DELIVERY,
    DATA,
    RankingOutcome,
    RankingResult,
    score_historical_photos,
)

# Avant l'import de FiftyOne : pas de télémétrie.
os.environ["FIFTYONE_DO_NOT_TRACK"] = "1"

import fiftyone as fo  # noqa: E402
import fiftyone.brain as fob  # noqa: E402
import fiftyone.core.odm as foo  # noqa: E402
from fiftyone import ViewField as F  # noqa: E402

DATASET = "cetolog-historique"
BRAIN_KEY = "cetaceanet"
SIMILARITY_KEY = "similarite"
ABSENT = 1_000_000


class CandidateRow(NamedTuple):
    """Représentation d'une photo candidate avec son rang et ses scores.

    Attributes
    ----------
    sample_id : str
        Identifiant FiftyOne de la photo de catalogue.
    rank : int
        Rang du dauphin dans la liste des candidats, à partir de 1. Les
        deux côtés d'un même dauphin portent le même rang.
    score : float
        Score du dauphin (meilleur cosinus tous côtés confondus).
    side_score : float or None
        Score du côté affiché. `None` si ce côté n'a pas été scoré.
    """

    sample_id: str
    rank: int
    score: float
    side_score: float | None


def _media(path: str | None) -> str | None:
    """Rend un chemin absolu, ou `None` si le côté n'a pas de photo.

    Parameters
    ----------
    path : str or None
        Chemin relatif à la racine du dépôt, ou `None`.

    Returns
    -------
    str or None
        Le chemin absolu, que FiftyOne sert sans copier la photo.
    """
    if path is None:
        return None
    return str(Path(path).resolve())


def _side_score(candidate_photo: dict, side: str) -> float | None:
    """Lit le score d'un côté, s'il est dans la photo candidate.

    Parameters
    ----------
    candidate_photo : dict
        Une photo candidate, avec les côtés présents.
    side : str
        `D` ou `G`.

    Returns
    -------
    float or None
        Le score, ou `None` si ce côté n'a pas été scoré.
    """
    if side not in candidate_photo:
        return None
    return float(candidate_photo[side])


def _side_score_label(side_score: float) -> str:
    """Formate un score pour l'afficher comme label.

    Parameters
    ----------
    side_score : float
        Score du côté.

    Returns
    -------
    str
        Le score, sans zéros inutiles.
    """
    return f"side_score={side_score:.4f}".rstrip("0").rstrip(".")


def _add_labels(
    sample: fo.Sample,
    individual: str,
    side: str,
    position: int,
    side_score: float | None,
    rank: int | None = None,
    match: bool = False,
) -> None:
    """Ajoute des labels dessinés sur chaque photo.

    Parameters
    ----------
    sample : fo.Sample
        Échantillon qui porte déjà ces primitives.
    individual : str
        Dauphin de la photo.
    side : str
        `D` ou `G`.
    position : int
        Position dans le groupe (à partir de 0). `0` pour la requête. Deux
        photos du même dauphin mais de côtés différents peuvent avoir des
        positions différentes selon leur score du côté.
    side_score : float or None
        Score de ce côté. `None` pour la requête, qui n'en a pas,
        ou pour une photo dont le côté n'a pas été scoré.
    rank : int or None, optional
        Rang du candidat à partir de 1. `None` pour la requête.
    match : bool, optional
        `True` si cette photo est le bon dauphin. Le label `match`
        n'est posé que dans ce cas.
    """
    sample["label_individual"] = fo.Classification(label=individual)
    sample["label_side"] = fo.Classification(label=side)
    if position > 0:
        sample["label_position"] = fo.Classification(label=f"position={position}")
    if rank is not None:
        sample["label_rank"] = fo.Classification(label=f"rank={rank}")
    if side_score is not None:
        sample["label_side_score"] = fo.Classification(label=_side_score_label(side_score))
    if match:
        sample["label_is_match"] = fo.Classification(label="match")


def _sample(result: RankingResult) -> fo.Sample:
    """Construit l'échantillon FiftyOne d'une photo d'historique classée.

    Parameters
    ----------
    result : RankingResult
        Une photo d'historique classée par `score_historical_photos`.

    Returns
    -------
    fo.Sample
        L'image principale est la photo d'historique.
    """
    sample = fo.Sample(filepath=_media(result.filepath))
    sample["ranking_outcome"] = result.ranking_outcome
    sample["match_rank"] = result.match_rank
    sample["side"] = result.side
    sample["delivery"] = result.delivery
    sample["individual"] = result.individual
    sample["match_score"] = result.match_score
    sample["first_false_score"] = result.first_false_score
    sample["position"] = 0
    _add_labels(sample, result.individual, result.side, 0, None)
    sample.tags = ["history"]
    return sample


def _catalogue_sample(photo: dict[str, str]) -> fo.Sample:
    """Construit l'échantillon d'une photo de catalogue.

    Parameters
    ----------
    photo : dict[str, str]
        Photo de catalogue, avec `chemin`, `individu` et `cote`.

    Returns
    -------
    fo.Sample
        L'image du catalogue, étiquetée `catalogue`.
    """
    sample = fo.Sample(filepath=_media(photo["chemin"]))
    sample["individual"] = photo["individu"]
    sample["side"] = photo["cote"]
    sample.tags = ["catalogue"]
    return sample

def _candidate_sample(
    catalogue_sample: fo.Sample,
    query_id: str,
    position: int,
    rank: int,
    side_score: float | None,
    match: bool,
    ranking_outcome: str | None = None,
) -> fo.Sample:
    """Copie une photo de catalogue dans le groupe de sa requête.

    Les photos de catalogue forment la bibliothèque de référence
    indexée : elles sont incorporées dans l'index de similarité et
    servent de source pour créer les copies candidates associées à
    chaque requête.

    Parameters
    ----------
    catalogue_sample : fo.Sample
        Photo de catalogue partagée, sans rang propre à une requête.
    query_id : str
        Identifiant FiftyOne de la photo d'historique (requête) qui a
        produit ce rang.
    position : int
        Position dans le groupe, à partir de 1. La requête porte 0. Deux
        photos du même dauphin mais de côtés différents peuvent avoir des
        positions différentes : elles sont triées par score du côté
        affiché, indépendamment de leur `match_rank` commun.
    rank : int
        Rang du dauphin dans la liste des candidats, à partir de 1. Les
        deux côtés d'un même dauphin portent le même rang.
    side_score : float or None
        Score du côté affiché. `None` si ce côté n'a pas été
        scoré. C'est cette valeur que le label dessine.
    match : bool
        `True` si `catalogue_sample` est le bon dauphin de la requête.
    ranking_outcome : str or None
        Classification de la requête (bien rangé, top mal rangé, ou hors
        top). Elle est recopiée pour que le filtre de classification
        garde la requête et ses copies candidates ensemble.

    Returns
    -------
    fo.Sample
        Nouvel échantillon rattaché à `query_id` avec sa propre `position`
        et `match_rank` (tous deux basés sur le `rank`). Les deux côtés
        d'un même dauphin portent le même rang. Le label de score porte
        le score du côté affiché.
    """
    sample = fo.Sample(filepath=catalogue_sample.filepath)
    sample["query_id"] = query_id
    sample["position"] = position
    sample["individual"] = catalogue_sample["individual"]
    sample["side"] = catalogue_sample["side"]
    if ranking_outcome is not None:
        sample["ranking_outcome"] = ranking_outcome
    _add_labels(
        sample,
        catalogue_sample["individual"],
        catalogue_sample["side"],
        position,
        side_score,
        rank=rank,
        match=match,
    )
    sample.tags = ["candidate"]
    return sample


def _candidate_rows(
    candidate_photos: Sequence[dict],
    catalogue_ids_by_individual_side: dict[tuple[str, str], str],
) -> list[CandidateRow]:
    """Décrit chaque photo de catalogue candidate, avec son rang et ses scores.

    Parameters
    ----------
    candidate_photos : Sequence[dict]
        Les photos candidates, le meilleur en tête. Chaque
        élément a `individu`, `score` (meilleur cosinus tous côtés
        confondus), et optionnellement `D` et `G` (cosinus de chaque côté).
    catalogue_ids_by_individual_side : dict[tuple[str, str], str]
        Identifiant FiftyOne de la photo de catalogue pour chaque
        couple (dauphin, côté).

    Returns
    -------
    list[CandidateRow]
        Une entrée par photo candidate avec son identifiant, rang,
        score global, et score du côté affiché. Le score le plus haut
        précède. À score égal, la droite précède la gauche. Un côté
        absent du catalogue est omis. Le score de côté vaut `None` si ce
        côté n'a pas été scoré, et cette photo passe en dernier.
    """
    rows = []
    for rank, candidate_photo in enumerate(candidate_photos, start=1):
        sides = []
        for side in SIDES:
            sample_id = catalogue_ids_by_individual_side.get(
                (candidate_photo["individu"], side)
            )
            if sample_id is None:
                continue
            sides.append(
                CandidateRow(
                    sample_id=sample_id,
                    rank=rank,
                    score=float(candidate_photo["score"]),
                    side_score=_side_score(candidate_photo, side),
                )
            )
        sides.sort(key=lambda row: (row.side_score is None, -(row.side_score or 0.0)))
        rows.extend(sides)
    return rows



def _true_match_outside_top(
    result: RankingResult, catalogue_ids_by_individual_side: dict[tuple[str, str], str]
) -> list[CandidateRow]:
    """Récupère les photos du bon dauphin quand il est hors du top 10.

    Quand le classement place le bon dauphin hors du top 10, cette
    fonction les désigne pour les afficher avec un marqueur `match`.
    Les deux côtés sont retournés s'ils existent au catalogue.

    Parameters
    ----------
    result : RankingResult
        Une photo d'historique classée.
    catalogue_ids_by_individual_side : dict[tuple[str, str], str]
        Identifiant de la photo de catalogue pour chaque couple
        (dauphin, côté).

    Returns
    -------
    list[CandidateRow]
        Les photos du bon dauphin avec son rang et son score, une par côté
        disponible au catalogue. Liste vide si le bon dauphin est déjà dans
        le top 10 ou manque du catalogue.
    """
    if result.ranking_outcome != RankingOutcome.OUTSIDE_TOP:
        return []
    
    rows = []
    for side in SIDES:
        sample_id = catalogue_ids_by_individual_side.get(
            (result.individual, side)
        )
        if sample_id is None:
            continue
        rows.append(
            CandidateRow(
                sample_id=sample_id,
                rank=result.match_rank,
                score=result.match_score,
                side_score=result.match_score,
            )
        )
    return rows


def _add_candidates(
    dataset: fo.Dataset,
    ranking_results: Sequence[RankingResult],
    query_ids: Sequence[str],
    catalogue_ids_by_individual_side: dict[tuple[str, str], str],
) -> None:
    """Ajoute, pour chaque requête, une copie de ses photos de catalogue.

    Parameters
    ----------
    dataset : fo.Dataset
        Dataset qui contient les photos d'historique et les photos de catalogue.
    ranking_results : Sequence[RankingResult]
        Photos d'historique classées (requêtes), dans le même ordre que
        `query_ids`.
    query_ids : Sequence[str]
        Identifiants FiftyOne des photos d'historique (requêtes),
        correspondant aux éléments de `ranking_results`.
    catalogue_ids_by_individual_side : dict[tuple[str, str], str]
        Identifiant de la photo de catalogue pour chaque couple
        (dauphin, côté).

    Notes
    -----
    Cette fonction effectue deux opérations :
        - met à jour les échantillons de requête avec `query_id`, `position` (0) et
        `ranking_outcome` ;
        - crée des copies des photos de catalogue avec leur position, rang et score
        propres à chaque requête.
    """
    if query_ids:
        query_samples = dataset.select(list(query_ids), ordered=True)
        query_samples.set_values("query_id", list(query_ids))
        query_samples.set_values("position", [0] * len(query_ids))
        query_samples.set_values("ranking_outcome", [
            result.ranking_outcome for result in ranking_results
        ])
    if not catalogue_ids_by_individual_side:
        return
    sources = {
        catalogue_sample.id: catalogue_sample
           for catalogue_sample in dataset.select(list(set(catalogue_ids_by_individual_side.values())))
    }
    copies = []
    for result, query_id in zip(ranking_results, query_ids, strict=True):
        rows = _candidate_rows(result.candidate_photos, catalogue_ids_by_individual_side)
        match_rows = _true_match_outside_top(result, catalogue_ids_by_individual_side)
        existing_sample_ids = {row.sample_id for row in rows}
        rows.extend(row for row in match_rows if row.sample_id not in existing_sample_ids)
        for position, row in enumerate(rows, start=1):
            catalogue_sample = sources[row.sample_id]
            copies.append(
                _candidate_sample(
                    catalogue_sample,
                    query_id,
                    position,
                    row.rank,
                    row.side_score,
                    catalogue_sample["individual"] == result.individual,
                    result.ranking_outcome,
                )
            )
    if copies:
        dataset.add_samples(copies)


def _order_results(
    ranking_results: Sequence[RankingResult], embeddings: np.ndarray
) -> tuple[list[RankingResult], np.ndarray]:
    """Ordonne les photos classées.

    Parameters
    ----------
    ranking_results : Sequence[RankingResult]
        Photos d'historique classées, une par ligne de `embeddings`.
    embeddings : np.ndarray
        Empreintes CetaceaNet, dans le même ordre que `ranking_results`.

    Returns
    -------
    tuple[list[RankingResult], np.ndarray]
        Hors top 10 d'abord, puis top 10 mal rangé, puis bien rangé.
        Dans chaque cas, pire rang en tête. Les empreintes suivent.
    """
    if len(ranking_results) == 0:
        return [], embeddings

    def sort_key(result: RankingResult) -> tuple[int, float]:
        if result.ranking_outcome == RankingOutcome.OUTSIDE_TOP:
            bucket = 0
        elif result.ranking_outcome == RankingOutcome.TOP_MISRANKED:
            bucket = 1
        else:
            bucket = 2
        rank = ABSENT if result.match_rank is None else result.match_rank
        return (bucket, -float(rank))

    order = sorted(
        range(len(ranking_results)), key=lambda index: sort_key(ranking_results[index])
    )
    ranking_results_ordered = [ranking_results[index] for index in order]
    return ranking_results_ordered, embeddings[order]


def _save_case_views(dataset: fo.Dataset) -> None:
    """Enregistre une vue groupée par requête pour chaque cas.

    Parameters
    ----------
    dataset : fo.Dataset
        Dataset dont la requête et ses copies partagent `query_id`,
        `ranking_outcome` et `ordre`.
    """
    descriptions = {
        RankingOutcome.OUTSIDE_TOP: (
            "Pire rang d'abord. Le bon dauphin suit les 10 plus proches"
        ),
        RankingOutcome.TOP_MISRANKED: "Pire rang d'abord",
        RankingOutcome.WELL_RANKED: "Rang 1",
    }
    for ranking_outcome in (
        RankingOutcome.OUTSIDE_TOP,
        RankingOutcome.TOP_MISRANKED,
        RankingOutcome.WELL_RANKED,
    ):
        dataset.save_view(
            ranking_outcome,
            dataset.match(F("ranking_outcome") == ranking_outcome).group_by(
                "query_id", order_by="position"
            ),
            description=descriptions[ranking_outcome],
        )


def _drop_dataset(name: str) -> None:
    """Supprime un dataset sans recharger ses échantillons.

    Parameters
    ----------
    name : str
        Nom du dataset FiftyOne.

    Notes
    -----
    `fo.delete_dataset` recharge le schéma. Un dataset écrit avec une
    classe `__main__` ne se charge plus, et cette voie ne peut plus le
    supprimer.
    """
    db = foo.get_db_conn()
    document = db.datasets.find_one({"name": name})
    if document is None:
        return
    for collection_name in (
        document.get("sample_collection_name"),
        document.get("frame_collection_name"),
    ):
        if collection_name:
            db.drop_collection(collection_name)
    view_ids = document.get("saved_views") or []
    if view_ids:
        db.views.delete_many({"_id": {"$in": view_ids}})
    workspace_ids = document.get("workspaces") or []
    if workspace_ids:
        db.workspaces.delete_many({"_id": {"$in": workspace_ids}})
    run_ids = []
    for field in ("annotation_runs", "brain_methods", "evaluations", "runs"):
        run_ids.extend((document.get(field) or {}).values())
    if run_ids:
        for run in db.runs.find({"_id": {"$in": run_ids}}, {"results": 1}):
            result_id = run.get("results")
            if result_id is not None:
                db["fs.files"].delete_one({"_id": result_id})
                db["fs.chunks"].delete_many({"files_id": result_id})
        db.runs.delete_many({"_id": {"$in": run_ids}})
    db.datasets.delete_one({"_id": document["_id"]})


def rebuild(
    ranking_results: Sequence[RankingResult],
    embeddings: np.ndarray,
    catalogue: Sequence[dict[str, str]],
    catalogue_embeddings: np.ndarray,
) -> fo.Dataset:
    """Reconstruit le dataset local, les vues et les empreintes.

    Valide que le nombre d'empreintes correspond au nombre de photos,
    ordonne les photos classées comme le notebook, puis popule le dataset
    FiftyOne avec les photos, les vues groupées et l'index de similarité.

    Parameters
    ----------
    ranking_results : Sequence[RankingResult]
        Photos d'historique classées (requêtes), une par échantillon.
    embeddings : np.ndarray
        Empreintes CetaceaNet des photos d'historique (requêtes), dans
        le même ordre que `ranking_results`. Les empreintes sont supposées
        être L2-normalisées.
    catalogue : Sequence[dict[str, str]]
        Photos de catalogue qui ont un côté.
    catalogue_embeddings : np.ndarray
        Empreintes CetaceaNet de `catalogue`, dans le même ordre. Les
        empreintes sont supposées être L2-normalisées.

    Returns
    -------
    fo.Dataset
        Le dataset `cetolog-historique`, avec une vue groupée par cas,
        l'index de similarité et la t-SNE.

    Raises
    ------
    ValueError
        Si le nombre d'empreintes ne correspond pas au nombre de photos
        classées ou de photos du catalogue.
    """
    if len(embeddings) != len(ranking_results):
        raise ValueError(
            "Les empreintes et les photos classées n'ont pas le même nombre."
        )
    if len(catalogue_embeddings) != len(catalogue):
        raise ValueError(
            "Les empreintes et les photos du catalogue n'ont pas le même "
            "nombre."
        )
    ranking_results, embeddings = _order_results(ranking_results, embeddings)
    if fo.dataset_exists(DATASET):
        _drop_dataset(DATASET)
    dataset = fo.Dataset(DATASET)
    dataset.persistent = True
    query_ids = dataset.add_samples([_sample(result) for result in ranking_results])
    catalogue_ids = dataset.add_samples(
        [_catalogue_sample(photo) for photo in catalogue]
    )
    catalogue_ids_by_individual_side = {
        (photo["individu"], photo["cote"]): sample_id
        for photo, sample_id in zip(catalogue, catalogue_ids, strict=True)
    }
    dataset.app_config.media_fields = ["filepath"]
    dataset.app_config.grid_media_field = "filepath"
    dataset.app_config.modal_media_field = "filepath"
    dataset.app_config.media_fallback = True
    dataset.save()
    indexed = np.vstack([embeddings, catalogue_embeddings])
    if len(indexed):
        fob.compute_similarity(
            dataset,
            embeddings=indexed,
            brain_key=SIMILARITY_KEY,
            metric="cosine",
        )
    _add_candidates(dataset, ranking_results, query_ids, catalogue_ids_by_individual_side)
    _save_case_views(dataset)
    if len(ranking_results) >= 2:
        # Calcule la t-SNE des empreintes CetaceaNet L2-normalisées.
        fob.compute_visualization(
            dataset.match_tags("history"),
            embeddings=embeddings,
            method="tsne",
            brain_key=BRAIN_KEY,
        )
    return dataset


def main() -> None:
    """Charge les données du disque et ouvre FiftyOne sur le dataset.

    Charge les photos d'historique classées et leurs empreintes via
    `score_historical_photos`, puis charge le catalogue et ses empreintes.
    Reconstruit le dataset FiftyOne `cetolog-historique` et affiche la vue
    des photos hors du top 10.
    """
    from demo.propositions import load

    data = Path(__file__).resolve().parents[1] / "data"
    ranking_results, embeddings = score_historical_photos(data)
    catalogue, catalogue_embeddings = load("catalogue", CATALOGUE_DELIVERY, data)
    dataset = rebuild(ranking_results, embeddings, catalogue, catalogue_embeddings)
    fo.launch_app(
        dataset.load_saved_view(RankingOutcome.OUTSIDE_TOP),
    ).wait()


if __name__ == "__main__":
    main()
