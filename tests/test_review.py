from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from demo.propositions import MODEL, TOP, load
from review.ranking import (
    CATALOGUE_DELIVERY,
    HISTORY_DELIVERIES,
    RankingOutcome,
    RankingResult,
    ranking_outcome,
    score_historical_photos,
)


def add_delivery(
    data: Path,
    kind: str,
    delivery: str,
    rows: list[tuple[str, str, str]],
    embeddings: list[list[float]],
) -> None:
    folder = data / "derived" / "embeddings" / kind / delivery
    folder.mkdir(parents=True)
    pd.DataFrame(rows, columns=["individu", "cote", "fichier_origine"]).to_csv(
        folder / "photos.csv", index=False
    )
    vectors = np.array(embeddings, dtype=float)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    np.save(folder / f"{MODEL}.npy", vectors / norms)


def named(results: list[RankingResult], filename: str) -> RankingResult:
    return next(result for result in results if Path(result.filepath).name == filename)


def load_catalogue(data: Path, delivery: str) -> tuple[list[dict], np.ndarray]:
    """Load catalogue photos, keeping only those with a side."""
    photos, embeddings = load("catalogue", delivery, data)
    sided = [
        (photo, embedding)
        for photo, embedding in zip(photos, embeddings, strict=True)
        if photo.get("cote") and photo["cote"].strip()
    ]
    if not sided:
        return [], np.empty((0, embeddings.shape[1]))
    photos, embeddings = zip(*sided, strict=True)
    return list(photos), np.array(embeddings)


@pytest.fixture
def excluded(tmp_path: Path) -> Path:
    add_delivery(
        tmp_path,
        "catalogue",
        "c",
        [
            ("TUTR0001", "D", "bon_d.jpg"),
            ("TUTR0003", "D", "sans_d.jpg"),
            ("TUTR0004", "D", "deux_a.jpg"),
            ("TUTR0004", "D", "deux_b.jpg"),
        ],
        [[1, 0], [0, 1], [1, 0], [0, 1]],
    )
    add_delivery(
        tmp_path,
        "historique",
        "h",
        [
            ("TUTR0001", "D", "meme.jpg"),
            ("TUTR0003", "G", "absent.jpg"),
            ("TUTR0004", "D", "garde.jpg"),
        ],
        [[1, 0], [1, 0], [1, 0]],
    )
    return tmp_path


@pytest.fixture
def ranked(tmp_path: Path) -> Path:
    add_delivery(
        tmp_path,
        "catalogue",
        "c",
        [
            ("TUTR0001", "D", "bon_d.jpg"),
            ("TUTR0001", "G", "bon_g.jpg"),
            ("TUTR0002", "D", "autre_d.jpg"),
            ("TUTR0002", "G", "autre_g.jpg"),
        ],
        [
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1],
        ],
    )
    add_delivery(
        tmp_path,
        "historique",
        "h",
        [
            ("TUTR0001", "D", "rang1.jpg"),
            ("TUTR0001", "D", "confus.jpg"),
        ],
        [
            [0.25, 0.85, 0.15, 0.1],
            [0.4, 0.2, 0.8, 0.2],
        ],
    )
    return tmp_path


def test_notebook_deliveries() -> None:
    assert HISTORY_DELIVERIES == (
        "2026-10-29_miraceti",
        "2026-11-06_bestof_20230307_sete",
    )
    assert CATALOGUE_DELIVERY == "2026-11-06_catalogue_tt"
    assert (
        RankingOutcome.WELL_RANKED.value,
        RankingOutcome.TOP_MISRANKED.value,
        RankingOutcome.OUTSIDE_TOP.value,
    ) == (
        "bien rangé",
        f"top {TOP}, mal rangé",
        f"hors top {TOP}",
    )


def test_case_follows_the_notebook_boundaries() -> None:
    assert ranking_outcome(1) == RankingOutcome.WELL_RANKED
    assert ranking_outcome(2) == RankingOutcome.TOP_MISRANKED
    assert ranking_outcome(TOP) == RankingOutcome.TOP_MISRANKED
    assert ranking_outcome(TOP + 1) == RankingOutcome.OUTSIDE_TOP
    assert ranking_outcome(None) == RankingOutcome.OUTSIDE_TOP


def test_excludes_the_catalogue_photo_and_a_missing_side(
    excluded: Path,
) -> None:
    ranking_results, vectors = score_historical_photos(excluded, ("h",), "c")
    names = {Path(result.filepath).name for result in ranking_results}

    # Only "garde.jpg" should be kept. "meme.jpg" is the same catalogue photo,
    # and "absent.jpg" has a missing side in the catalogue
    assert names == {"garde.jpg"}
    assert vectors.shape[0] == len(ranking_results)


def test_rank_one_scores_and_catalogue_paths(ranked: Path) -> None:
    ranking_results, vectors = score_historical_photos(ranked, ("h",), "c")
    result = named(ranking_results, "rang1.jpg")
    root = ranked / "curated"

    assert vectors.shape[0] == len(ranking_results)
    assert result.ranking_outcome == RankingOutcome.WELL_RANKED
    assert result.match_rank == 1
    assert result.side == "D"
    assert result.delivery == "h"
    assert result.individual == "TUTR0001"
    assert result.match_score > result.first_false_score
    assert result.filepath == str(
        root / "historique" / "photos" / "h" / "TUTR0001" / "rang1.jpg"
    )
    first = result.candidate_photos[0]
    assert first["individu"] == "TUTR0001"
    assert first["G"] > first["D"]
    assert result.match_score == pytest.approx(first["score"])


def test_confusion_uses_the_first_candidate_side(ranked: Path) -> None:
    ranking_results, _vectors = score_historical_photos(ranked, ("h",), "c")
    result = named(ranking_results, "confus.jpg")

    assert result.ranking_outcome == RankingOutcome.TOP_MISRANKED
    assert result.match_rank == 2
    assert result.match_score < result.first_false_score
    assert result.candidate_photos[0]["individu"] == "TUTR0002"
    assert result.first_false_score == pytest.approx(
        result.candidate_photos[0]["score"]
    )


def test_hors_top_ten_sorts_the_true_dolphin_after_the_rest(
    tmp_path: Path,
) -> None:
    rows = [("TUTR0001", "D", "bon_d.jpg")]
    vectors = [[1.0, 0.0, 0.0, 0.0]]
    for number in range(1, TOP + 1):
        rows.append((f"TUTR{number + 1:04d}", "D", f"d{number:02d}.jpg"))
        vectors.append([0.0, 0.0, 1.0, 0.0])
    add_delivery(tmp_path, "catalogue", "c", rows, vectors)
    add_delivery(
        tmp_path,
        "historique",
        "h",
        [("TUTR0001", "D", "loin.jpg")],
        [[0.5, 0.0, 0.7, 0.0]],
    )

    ranking_results, _vectors = score_historical_photos(tmp_path, ("h",), "c")
    result = ranking_results[0]

    assert result.ranking_outcome == RankingOutcome.OUTSIDE_TOP
    assert result.match_rank == TOP + 1
    assert result.match_score < result.first_false_score
    assert len(result.candidate_photos) == TOP
    assert "TUTR0001" not in [
        candidate["individu"] for candidate in result.candidate_photos
    ]


def test_deliveries_are_stacked_in_order(tmp_path: Path) -> None:
    add_delivery(
        tmp_path,
        "catalogue",
        "c",
        [("TUTR0001", "D", "a.jpg"), ("TUTR0002", "D", "b.jpg")],
        [[1, 0], [0, 1]],
    )
    add_delivery(
        tmp_path, "historique", "h1", [("TUTR0001", "D", "a.jpg")], [[0.8, 0.6]]
    )
    add_delivery(
        tmp_path, "historique", "h2", [("TUTR0002", "D", "b.jpg")], [[0.6, 0.8]]
    )

    ranking_results, _vectors = score_historical_photos(tmp_path, ("h1", "h2"), "c")

    assert [result.delivery for result in ranking_results] == ["h1", "h2"]
    assert [result.individual for result in ranking_results] == [
        "TUTR0001",
        "TUTR0002",
    ]


def test_load_catalogue_keeps_only_sided_photos(tmp_path: Path) -> None:
    add_delivery(
        tmp_path,
        "catalogue",
        "c",
        [
            ("TUTR0001", "D", "droite.jpg"),
            ("TUTR0001", "G", "gauche.jpg"),
            ("TUTR0002", "", "illisible.jpg"),
        ],
        [[1, 0], [0, 1], [1, 1]],
    )

    photos, embeddings = load_catalogue(tmp_path, "c")

    assert [photo["fichier_origine"] for photo in photos] == [
        "droite.jpg",
        "gauche.jpg",
    ]
    assert embeddings.shape == (2, 2)


def test_review_order_sorts_each_case() -> None:
    pytest.importorskip("fiftyone")
    from review.app import _order_results

    ranking_results = [
        RankingResult(
            RankingOutcome.WELL_RANKED,
            1,
            "D",
            "h",
            "premier",
            0.9,
            0.2,
            "/path/to/file1.jpg",
            [],
        ),
        RankingResult(
            RankingOutcome.OUTSIDE_TOP,
            30,
            "D",
            "h",
            "other",
            0.5,
            0.6,
            "/path/to/file2.jpg",
            [],
        ),
        RankingResult(
            RankingOutcome.OUTSIDE_TOP,
            None,
            "D",
            "h",
            "other2",
            None,
            0.7,
            "/path/to/file3.jpg",
            [],
        ),
        RankingResult(
            RankingOutcome.TOP_MISRANKED,
            2,
            "D",
            "h",
            "other3",
            0.6,
            0.65,
            "/path/to/file4.jpg",
            [],
        ),
        RankingResult(
            RankingOutcome.WELL_RANKED,
            1,
            "D",
            "h",
            "second",
            0.95,
            0.3,
            "/path/to/file5.jpg",
            [],
        ),
        RankingResult(
            RankingOutcome.TOP_MISRANKED,
            8,
            "D",
            "h",
            "other4",
            0.4,
            0.5,
            "/path/to/file6.jpg",
            [],
        ),
    ]
    embeddings = np.eye(len(ranking_results))

    ordered, vectors = _order_results(ranking_results, embeddings)

    assert [(item.ranking_outcome, item.match_rank) for item in ordered] == [
        (RankingOutcome.OUTSIDE_TOP, None),
        (RankingOutcome.OUTSIDE_TOP, 30),
        (RankingOutcome.TOP_MISRANKED, 8),
        (RankingOutcome.TOP_MISRANKED, 2),
        (RankingOutcome.WELL_RANKED, 1),
        (RankingOutcome.WELL_RANKED, 1),
    ]
    assert [item.individual for item in ordered[-2:]] == [
        "premier",
        "second",
    ]
    assert np.array_equal(vectors, embeddings[[2, 1, 5, 3, 0, 4]])


def test_case_view_groups_a_query_with_its_neighbours(
    tmp_path: Path,
) -> None:
    pytest.importorskip("fiftyone")
    import fiftyone as fo
    from PIL import Image

    from review.app import (
        _add_candidates,
        _catalogue_sample,
        _sample,
        _save_case_views,
    )

    image = tmp_path / "query.jpg"
    Image.new("RGB", (8, 8), (30, 30, 30)).save(image)
    result: RankingResult = RankingResult(
        ranking_outcome=RankingOutcome.WELL_RANKED,
        match_rank=1,
        side="D",
        delivery="h",
        individual="TUTR0001",
        match_score=0.9,
        first_false_score=0.2,
        filepath=str(image),
        candidate_photos=[
            {"individu": "TUTR0001", "score": 0.9, "D": 0.4, "G": 0.9},
            {"individu": "TUTR0002", "score": 0.2, "D": 0.2},
        ],
    )
    other: RankingResult = RankingResult(
        ranking_outcome=RankingOutcome.OUTSIDE_TOP,
        match_rank=30,
        side="D",
        delivery="h",
        individual="TUTR0009",
        match_score=0.1,
        first_false_score=0.4,
        filepath=str(image),
        candidate_photos=[{"individu": "TUTR0002", "score": 0.4, "D": 0.4}],
    )
    droite = {"individu": "TUTR0001", "cote": "D", "chemin": str(image)}
    gauche = {"individu": "TUTR0001", "cote": "G", "chemin": str(image)}
    autre = {"individu": "TUTR0002", "cote": "D", "chemin": str(image)}
    bon = {"individu": "TUTR0009", "cote": "D", "chemin": str(image)}
    autre_cote = {"individu": "TUTR0009", "cote": "G", "chemin": str(image)}
    name = "cetolog-review-vue"
    if fo.dataset_exists(name):
        fo.delete_dataset(name)
    dataset = fo.Dataset(name)
    dataset.persistent = True
    try:
        query_ids = dataset.add_samples([_sample(result), _sample(other)])
        catalogue_ids = dataset.add_samples(
            [
                _catalogue_sample(droite),
                _catalogue_sample(gauche),
                _catalogue_sample(autre),
                _catalogue_sample(bon),
                _catalogue_sample(autre_cote),
            ]
        )
        catalogue_ids_by_individu_cote = {
            ("TUTR0001", "D"): catalogue_ids[0],
            ("TUTR0001", "G"): catalogue_ids[1],
            ("TUTR0002", "D"): catalogue_ids[2],
            ("TUTR0009", "D"): catalogue_ids[3],
            ("TUTR0009", "G"): catalogue_ids[4],
        }
        _add_candidates(
            dataset,
            [result, other],
            query_ids,
            catalogue_ids_by_individu_cote,
        )
        _save_case_views(dataset)
        # Verify that all three views are created with the expected ranking outcomes
        assert dataset.list_saved_views() == [
            RankingOutcome.OUTSIDE_TOP.value,
            RankingOutcome.TOP_MISRANKED.value,
            RankingOutcome.WELL_RANKED.value,
        ]
        # Verify that WELL_RANKED view groups results
        groups = list(
            dataset.load_saved_view(
                RankingOutcome.WELL_RANKED.value
            ).iter_dynamic_groups()
        )
        assert len(groups) == 1
        shown = list(groups[0])
        # First sample is the query
        assert shown[0].id == query_ids[0]
        assert shown[0]["position"] == 0
        # Verify candidates are grouped with the query
        assert len(shown) > 1
    finally:
        fo.delete_dataset(name)
