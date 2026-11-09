import csv

import numpy as np
import pandas as pd
import pytest

from demo.propositions import MODEL, catalogue_photos, latest, load, propose, write


def add_delivery(data, kind, delivery, rows, embeddings):
    folder = data / "derived" / "embeddings" / kind / delivery
    folder.mkdir(parents=True)
    pd.DataFrame(rows, columns=["individu", "cote", "fichier_origine"]).to_csv(folder / "photos.csv", index=False)
    vectors = np.array(embeddings, dtype=float)
    np.save(folder / f"{MODEL}.npy", vectors / np.linalg.norm(vectors, axis=1, keepdims=True))


@pytest.fixture
def data(tmp_path):
    add_delivery(tmp_path, "catalogue", "c", [
        ("TUTR0001", "D", "a.jpg"),
        ("TUTR0002", "D", "b.jpg"),
        ("TUTR0003", "", "illisible.jpg"),
    ], [[1, 0], [0, 1], [1, 1]])
    add_delivery(tmp_path, "best_of", "b", [
        ("IND2", "D", "x.jpg"),
        ("IND10", "D", "y.jpg"),
    ], [[0.8, 0.6], [1, 0]])
    return tmp_path


def test_load_keeps_an_empty_side_and_builds_the_path(data):
    photos, embeddings = load("catalogue", "c", data)

    assert photos[2]["cote"] == ""
    assert photos[0]["chemin"] == str(data / "curated" / "catalogue" / "photos" / "c" / "TUTR0001" / "a.jpg")
    assert embeddings.shape == (3, 2)


def test_latest_takes_the_most_recent_delivery(data):
    add_delivery(data, "catalogue", "d", [("TUTR0001", "D", "a.jpg")], [[1, 0]])

    assert latest("catalogue", data) == "d"


def test_propose_ranks_candidates_and_orders_individuals(data):
    propositions = propose("b", "c", data)

    assert list(propositions) == ["IND2", "IND10"]
    candidates = propositions["IND2"]["candidats"]
    assert [candidate["individu"] for candidate in candidates] == ["TUTR0001", "TUTR0002"]
    assert candidates[0]["score"] == pytest.approx(0.8)


def test_propose_searches_the_opposite_side(tmp_path):
    add_delivery(tmp_path, "catalogue", "c", [("TUTR0001", "D", "a.jpg")], [[1, 0]])
    add_delivery(tmp_path, "best_of", "b", [("IND1", "G", "x.jpg")], [[0.8, 0.6]])

    candidates = propose("b", "c", tmp_path)["IND1"]["candidats"]

    assert [candidate["individu"] for candidate in candidates] == ["TUTR0001"]
    assert candidates[0]["score"] == pytest.approx(0.8)


def test_propose_scores_a_candidate_with_its_best_side(tmp_path):
    add_delivery(tmp_path, "catalogue", "c", [("TUTR0001", "D", "a.jpg"), ("TUTR0001", "G", "b.jpg")], [[1, 0], [0, 1]])
    add_delivery(tmp_path, "best_of", "b", [("IND1", "D", "x.jpg")], [[0.8, 0.6]])

    candidate = propose("b", "c", tmp_path)["IND1"]["candidats"][0]

    assert (candidate["D"], candidate["G"]) == pytest.approx((0.8, 0.6))
    assert candidate["score"] == pytest.approx(0.8)


def test_propose_breaks_ties_by_identifier(tmp_path):
    names = [f"TUTR{number:04d}" for number in range(1, 21)]
    add_delivery(tmp_path, "catalogue", "c", [(name, "D", f"{name}.jpg") for name in reversed(names)], [[1, 0]] * len(names))
    add_delivery(tmp_path, "best_of", "b", [("IND1", "D", "x.jpg")], [[0.8, 0.6]])

    candidates = propose("b", "c", tmp_path)["IND1"]["candidats"]

    assert [candidate["individu"] for candidate in candidates] == names


def test_propose_sets_aside_the_same_photo(data):
    proposition = propose("b", "c", data)["IND10"]

    assert proposition["reponse"] == ["TUTR0001"]
    assert "TUTR0001" not in [candidate["individu"] for candidate in proposition["candidats"]]


def test_catalogue_photos_finds_a_photo_by_dolphin_and_side(data):
    photos = catalogue_photos(load("catalogue", "c", data)[0])

    assert photos[("TUTR0002", "D")].endswith("b.jpg")


def test_write_saves_the_candidates(data):
    output = write("b", "c", data)

    with open(output, encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    first = rows[0]
    assert (first["individu"], first["rang"], first["candidat"]) == ("IND2", "1", "TUTR0001")
    assert (first["score"], first["cosinus_D"], first["cosinus_G"]) == ("0.8", "0.8", "")
