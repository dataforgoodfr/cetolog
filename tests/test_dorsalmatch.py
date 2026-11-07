import subprocess
import sys

import numpy as np
import pytest

import dorsalmatch


# Faux vecteurs de norme 1
def unit_vectors(*rows):
    vectors = np.array(rows, dtype=float)
    return vectors / np.linalg.norm(vectors, axis=1, keepdims=True)


def test_unknown_model():
    pytest.importorskip("torch")
    with pytest.raises(ValueError, match="Modèles disponibles"):
        dorsalmatch.Embedder("inconnu")


def test_search_in_catalogue():
    results = dorsalmatch.search(unit_vectors([1, 0.05]), unit_vectors([0, 1], [1, 0]), k=1)
    assert results[0][0][0] == 1


def test_neighbors_exclude_the_photo_itself():
    results = dorsalmatch.neighbors(unit_vectors([1, 0], [1, 0.1], [0, 1]), 2)
    assert [closest[0][0] for closest in results] == [1, 0, 1]
    assert all(neighbor != photo for photo, closest in enumerate(results) for neighbor, _ in closest)


def test_evaluate_two_separate_groups():
    embeddings = unit_vectors([1, 0], [1, 0.1], [0, 1], [0.1, 1])
    scores, counted = dorsalmatch.evaluate(embeddings, np.array(["a", "a", "b", "b"]))
    assert scores == {"top-1": 1.0, "top-5": 1.0, "top-10": 1.0, "mAP": 1.0}
    assert counted == 4


def test_evaluate_ignores_photos_without_a_correct_result():
    assert dorsalmatch.evaluate(unit_vectors([1, 0], [1, 0.1], [0, 1]), np.array(["a", "a", "b"]))[1] == 2


def test_pairs():
    same, different = dorsalmatch.pairs(unit_vectors([1, 0], [1, 0], [0, 1]), np.array(["a", "a", "b"]))
    assert same.tolist() == [1.0]
    assert different.tolist() == [0.0, 0.0]


def test_library_needs_neither_s3_nor_torch():
    code = "import sys, dorsalmatch; sys.exit('boto3' in sys.modules or 'torch' in sys.modules)"
    assert subprocess.run([sys.executable, "-c", code], check=False).returncode == 0
