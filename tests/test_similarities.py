import pytest

from pipeline.similarities import best_threshold, top_k


def test_top_k_and_threshold():
    rows = [
        {"rang": 1, "score_premier": 0.9, "score_premier_faux": 0.4},
        {"rang": 3, "score_premier": 0.8, "score_premier_faux": 0.5},
        {"rang": "", "score_premier": 0.6, "score_premier_faux": 0.6},
    ]
    assert top_k(rows) == {
        "top-1": pytest.approx(1 / 3),
        "top-5": pytest.approx(2 / 3),
        "top-10": pytest.approx(2 / 3),
    }
    # Seuil 0.6 : les 3 connus gardés, 2 nouveaux sur 3 repérés
    assert best_threshold(rows) == (0.6, 1.0, pytest.approx(2 / 3))
