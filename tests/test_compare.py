from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from review.compare import best_side, heatmap_path, read_heatmap
from review.heatmaps import by_interest


def test_best_side_takes_the_higher_scored_side() -> None:
    assert best_side({"individu": "A", "score": 0.6, "D": 0.4, "G": 0.6}) == "G"
    assert best_side({"individu": "A", "score": 0.4, "D": 0.4}) == "D"


def test_disagreements_come_first() -> None:
    models = ("a", "b")

    def entry(name, rank_a, rank_b):
        return {"name": name, "a": {"rang": rank_a}, "b": {"rang": rank_b}}

    entries = [entry("both", 1, 1), entry("none", 5, 30), entry("split", 1, 12)]
    assert [e["name"] for e in by_interest(entries, models)] == [
        "split",
        "none",
        "both",
    ]


def test_heatmap_path_is_per_model_and_direction(tmp_path: Path) -> None:
    a, b = {"sha256": "a" * 64}, {"sha256": "b" * 64}
    assert heatmap_path(tmp_path, "m", a, b) != heatmap_path(tmp_path, "m", b, a)
    assert heatmap_path(tmp_path, "m", a, b).parent.name == "m"


def test_read_heatmap_normalises_and_skips_missing(tmp_path: Path) -> None:
    pytest.importorskip("fiftyone")
    a, b = {"sha256": "a" * 64}, {"sha256": "b" * 64}
    assert read_heatmap(tmp_path, "m", a, b) is None

    path = heatmap_path(tmp_path, "m", a, b)
    path.parent.mkdir(parents=True)
    np.save(path, np.array([[0.0, 2.0], [1.0, 0.5]]))
    heatmap = read_heatmap(tmp_path, "m", a, b)
    assert heatmap.map.shape == (256, 256)
    assert heatmap.map.max() == 255


def test_dolphin_share_is_one_for_a_uniform_map() -> None:
    from review.compare import dolphin_share

    mask = np.zeros((40, 60), dtype=bool)
    mask[10:30, 20:40] = True
    assert dolphin_share(np.ones((12, 12)), mask) == pytest.approx(1.0, rel=0.02)


def test_dolphin_share_rewards_heat_on_the_dolphin() -> None:
    from review.compare import dolphin_share

    mask = np.zeros((40, 40), dtype=bool)
    mask[:, :20] = True  # moitié gauche : le dauphin
    on_dolphin = np.zeros((4, 4))
    on_dolphin[:, :2] = 1
    on_water = on_dolphin[:, ::-1]
    assert dolphin_share(on_dolphin, mask) > 1.5
    assert dolphin_share(on_water, mask) < 0.5
    assert dolphin_share(np.zeros((4, 4)), mask) is None
    assert dolphin_share(on_dolphin, None) is None


def test_each_photo_is_masked_once() -> None:
    from review.masks import photos_to_mask

    a, b, c = ({"sha256": s * 64} for s in "abc")
    entries = [
        {"photo": a, "bon": b, "m1": {"faux": c}, "m2": {"faux": c}},
        {"photo": b, "bon": b, "m1": {"faux": a}, "m2": {"faux": c}},
    ]
    assert len(photos_to_mask(entries, ("m1", "m2"))) == 3
