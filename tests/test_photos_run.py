import csv
import io
import zipfile

import pytest
from PIL import Image

from pipeline.photos.run import run

DELIVERY = "2026-10-29_miraceti"


def image_bytes(color):
    buffer = io.BytesIO()
    Image.new("RGB", (4, 3), color).save(buffer, "JPEG")
    return buffer.getvalue()


# Un dossier data/ avec une petite livraison, et les fichiers ajoutés par macOS
@pytest.fixture
def data(tmp_path):
    raw = tmp_path / "raw" / "photos"
    raw.mkdir(parents=True)
    with zipfile.ZipFile(raw / f"{DELIVERY}_photos.zip", "w") as archive:
        archive.writestr("TUTR0025/D_TUTR0025_20111016_a.jpg", image_bytes("white"))
        archive.writestr("TUTR0118/G_TUTR0118_20120315_b.jpg", image_bytes("black"))
        archive.writestr("__MACOSX/TUTR0118/._G_TUTR0118_20120315_b.jpg", b"pas une image")
    return tmp_path


def manifest_rows(data):
    with open(data / "curated" / "manifests" / f"{DELIVERY}.csv", encoding="utf-8") as file:
        return list(csv.DictReader(file))


# Du zip à data/curated/
def test_new_zip_builds_curated(data):
    run(data)

    photos = data / "curated" / "photos" / DELIVERY
    assert (photos / "TUTR0025" / "D_TUTR0025_20111016_a.jpg").exists()
    assert (photos / "TUTR0118" / "G_TUTR0118_20120315_b.jpg").exists()
    assert len(list(photos.rglob("*.jpg"))) == 2
    rows = manifest_rows(data)
    assert len(rows) == 2
    assert {row["livraison"] for row in rows} == {DELIVERY}


def test_processed_zip_is_skipped(data, capsys):
    run(data)
    capsys.readouterr()
    run(data)

    assert "déjà traitée" in capsys.readouterr().out


def test_interrupted_run_resumes(data):
    run(data)
    (data / "curated" / "manifests" / f"{DELIVERY}.csv").unlink()
    run(data)

    assert len(manifest_rows(data)) == 2


def test_badly_named_zip_is_ignored(data, capsys):
    (data / "raw" / "photos" / "Smash.zip").write_bytes(b"")
    run(data)

    assert "ignoré" in capsys.readouterr().out
    assert len(manifest_rows(data)) == 2


def test_no_zip_says_so(tmp_path, capsys):
    run(tmp_path)

    assert "Aucun zip" in capsys.readouterr().out
