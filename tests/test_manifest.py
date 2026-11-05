from datetime import date

import pytest
from PIL import Image

from pipeline.photos.manifest import build_manifest, read_filename


# Nom du fichier
def test_normal_name():
    assert read_filename("D_TUTR0025_20111016_SOSGB_DSC02138.jpg") == ("D", "TUTR0025", date(2011, 10, 16))


def test_names_found_in_the_delivery():
    assert read_filename("G_TUTR003820180913_x.jpg") == ("G", "TUTR0038", date(2018, 9, 13))
    assert read_filename("D__TUTR025_20111016_x.jpg") == ("D", "TUTR0025", date(2011, 10, 16))
    assert read_filename("D_TUTR0025_200627_x.jpg") == ("D", "TUTR0025", date(2020, 6, 27))
    assert read_filename("D_TUTR0025_x.jpg") == ("D", "TUTR0025", None)
    assert read_filename("photo.jpg") == ("", None, None)


# Construction du manifeste
def test_manifest_reports_anomalies(tmp_path):
    folder = tmp_path / "TUTR0155"
    folder.mkdir()
    Image.new("RGB", (4, 3)).save(folder / "D_TUTR0153_20120315_a.jpg")
    Image.new("RGB", (4, 3)).save(folder / "D_TUTR0155_20120315_b.jpg")
    rows = build_manifest(tmp_path)

    assert [row["individu"] for row in rows] == ["TUTR0155", "TUTR0155"]
    assert "nom de fichier TUTR0153 ≠ dossier TUTR0155" in rows[0]["anomalies"]
    assert "doublon exact" in rows[1]["anomalies"]


def test_unreadable_image_is_an_anomaly(tmp_path):
    folder = tmp_path / "TUTR0155"
    folder.mkdir()
    (folder / "D_TUTR0155_20120315_a.jpg").write_bytes(b"pas une image")

    assert build_manifest(tmp_path)[0]["anomalies"] == "image illisible"


def test_macos_files_are_ignored(tmp_path):
    folder = tmp_path / "__MACOSX" / "TUTR0155"
    folder.mkdir(parents=True)
    (folder / "._D_TUTR0155_20120315_a.jpg").write_bytes(b"pas une image")

    assert build_manifest(tmp_path) == []


def test_photo_outside_a_dolphin_folder_is_refused(tmp_path):
    folder = tmp_path / "photos"
    folder.mkdir()
    Image.new("RGB", (4, 3)).save(folder / "D_TUTR0155_20120315_a.jpg")

    with pytest.raises(ValueError, match="Dossier de dauphin invalide"):
        build_manifest(tmp_path)
