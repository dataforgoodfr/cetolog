import csv
import io
import zipfile

import numpy as np
import pytest
from PIL import Image

import dorsalmatch
from pipeline import bootstrap, run


# Faux modèle : l'empreinte est la couleur moyenne
class ColorEmbedder:
    def __init__(self, name):
        self.name = name

    def embed(self, paths):
        colors = np.array([np.asarray(Image.open(path).convert("RGB"), dtype=float).mean(axis=(0, 1)) for path in paths])
        return colors / np.linalg.norm(colors, axis=1, keepdims=True)


@pytest.fixture(autouse=True)
def fake_model(monkeypatch):
    monkeypatch.setattr(dorsalmatch, "Embedder", ColorEmbedder, raising=False)


def image_bytes(color):
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), color).save(buffer, "PNG")
    return buffer.getvalue()


def make_zip(data, kind, delivery, files):
    folder = data / "raw" / kind
    folder.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(folder / f"{delivery}.zip", "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)


def test_run_needs_the_catalogue_first(tmp_path):
    with pytest.raises(RuntimeError, match="pipeline.bootstrap"):
        run.run(tmp_path)


def test_bootstrap_then_run_gives_propositions(tmp_path):
    make_zip(tmp_path, "catalogue", "2026-11-06_catalogue", {
        "DD/DD_TUTR0001_a.png": image_bytes((255, 0, 0)),
        "DD/DD_TUTR0002_b.png": image_bytes((0, 255, 0)),
    })
    bootstrap.run(tmp_path)
    assert (tmp_path / "derived" / "embeddings" / "catalogue" / "2026-11-06_catalogue" / "cetaceanet.npy").exists()

    make_zip(tmp_path, "best_of", "2026-11-07_bestof_sete", {
        "IND/IND1/D_1_20261107_x.png": image_bytes((200, 80, 0)),
    })
    run.run(tmp_path)

    with open(tmp_path / "derived" / "propositions" / "2026-11-07_bestof_sete.csv", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    assert [(row["individu"], row["rang"], row["candidat"]) for row in rows] == [("IND1", "1", "TUTR0001"), ("IND1", "2", "TUTR0002")]
    assert rows[0]["catalogue"] == "2026-11-06_catalogue"


def test_processed_best_of_is_skipped(tmp_path, capsys):
    make_zip(tmp_path, "catalogue", "c", {"DD/DD_TUTR0001_a.png": image_bytes((255, 0, 0))})
    bootstrap.run(tmp_path)
    make_zip(tmp_path, "best_of", "b", {"IND/IND1/D_1_20261107_x.png": image_bytes((200, 80, 0))})
    run.run(tmp_path)
    capsys.readouterr()
    run.run(tmp_path)

    assert "propositions déjà faites" in capsys.readouterr().out
