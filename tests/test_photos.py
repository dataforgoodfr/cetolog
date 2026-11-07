import csv
import io
import zipfile

from PIL import Image

from pipeline.photos import best_of, catalogue


def image_bytes(color):
    buffer = io.BytesIO()
    Image.new("RGB", (4, 3), color).save(buffer, "JPEG")
    return buffer.getvalue()


# Un zip dans data/raw/<type>/, avec les fichiers donnés
def make_zip(data, kind, delivery, files):
    folder = data / "raw" / kind
    folder.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(folder / f"{delivery}.zip", "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)


def manifest_rows(data, kind, delivery):
    with open(data / "curated" / kind / "manifests" / f"{delivery}.csv", encoding="utf-8") as file:
        return list(csv.DictReader(file))


# Catalogue : tout est dans le nom, les dossiers ne comptent pas
def test_catalogue_reads_names_and_reports_anomalies(tmp_path):
    make_zip(tmp_path, "catalogue", "2026-11-06_catalogue_tt", {
        "Catalogue Tt/DD_20260127/DD_TUTR0001_img_8940.jpg": image_bytes("white"),
        "Catalogue Tt/DG_20260127/DG/DG_TUTR0001_img8962.jpg": image_bytes("black"),
        "Catalogue Tt/DD_20260127/DD_TUTR539_20240813_PNCal-0055.jpg": image_bytes("red"),
        "Catalogue Tt/DG_20260127/DG/DG_TUTR0004_sln-35.jpg.jpg": image_bytes("blue"),
        "Catalogue Tt/DG_20260127/DG/DG_TTGC2050_fd-galeria_070501_041.jpg": image_bytes("green"),
        "Catalogue Tt/DG_20260127/DG/DG_TUTR05558_20220428_x.jpg": image_bytes("gray"),
    })
    catalogue.run(tmp_path)

    rows = {row["fichier_origine"]: row for row in manifest_rows(tmp_path, "catalogue", "2026-11-06_catalogue_tt")}
    assert (rows["DD_TUTR0001_img_8940.jpg"]["individu"], rows["DD_TUTR0001_img_8940.jpg"]["cote"]) == ("TUTR0001", "D")
    assert (rows["DG_TUTR0001_img8962.jpg"]["individu"], rows["DG_TUTR0001_img8962.jpg"]["cote"]) == ("TUTR0001", "G")
    assert rows["DD_TUTR539_20240813_PNCal-0055.jpg"]["individu"] == "TUTR0539"
    assert rows["DG_TUTR0004_sln-35.jpg.jpg"]["anomalies"] == "double extension"
    assert rows["DG_TTGC2050_fd-galeria_070501_041.jpg"]["anomalies"] == "identifiant hors TUTR"
    assert rows["DG_TUTR05558_20220428_x.jpg"]["individu"] == "illisible"

    photos = tmp_path / "curated" / "catalogue" / "photos" / "2026-11-06_catalogue_tt"
    assert (photos / "TUTR0001" / "DD_TUTR0001_img_8940.jpg").exists()
    assert (photos / "TUTR0001" / "DG_TUTR0001_img8962.jpg").exists()


def test_catalogue_flags_two_photos_on_the_same_side(tmp_path):
    make_zip(tmp_path, "catalogue", "c", {
        "DD/DD_TUTR0558_a.jpg": image_bytes("white"),
        "DD/DD_TUTR0558_b.jpg": image_bytes("black"),
    })
    catalogue.run(tmp_path)

    assert {row["anomalies"] for row in manifest_rows(tmp_path, "catalogue", "c")} == {"plusieurs photos pour ce côté"}


# Best-of : seulement les dossiers IND, DD/ et DG/ sont des copies
def test_best_of_keeps_ind_folders_only(tmp_path):
    make_zip(tmp_path, "best_of", "2026-11-06_bestof_20230307_sete", {
        "Bestof_20230307_Sete/DD/D_3_20230307_Sete_X_IMG_8484.jpg": image_bytes("white"),
        "Bestof_20230307_Sete/IND/IND3/D_3_20230307_Sete_X_IMG_8484.jpg": image_bytes("white"),
        "Bestof_20230307_Sete/IND/IND3/G_3_20230307_Sete_X_IMG_4523.jpg": image_bytes("black"),
        "Bestof_20230307_Sete/IND/IND17/D_7_20230307_Sete_X_IMG_4495.jpg": image_bytes("red"),
    })
    best_of.run(tmp_path)

    rows = manifest_rows(tmp_path, "best_of", "2026-11-06_bestof_20230307_sete")
    assert [(row["individu"], row["cote"]) for row in rows] == [("IND17", "D"), ("IND3", "D"), ("IND3", "G")]
    assert rows[1]["date_nom"] == "2023-03-07"
    assert rows[0]["anomalies"] == "nom de fichier 7 ≠ dossier IND17"

    photos = tmp_path / "curated" / "best_of" / "photos" / "2026-11-06_bestof_20230307_sete"
    assert len(list(photos.rglob("*.jpg"))) == 3


# Ce qui est commun aux trois
def test_processed_zip_is_skipped(tmp_path, capsys):
    make_zip(tmp_path, "catalogue", "a", {"DD/DD_TUTR0025_a.jpg": image_bytes("white")})
    catalogue.run(tmp_path)
    capsys.readouterr()
    catalogue.run(tmp_path)

    assert "déjà traitée" in capsys.readouterr().out


def test_interrupted_run_resumes(tmp_path):
    make_zip(tmp_path, "catalogue", "a", {"DD/DD_TUTR0025_a.jpg": image_bytes("white")})
    catalogue.run(tmp_path)
    (tmp_path / "curated" / "catalogue" / "manifests" / "a.csv").unlink()
    catalogue.run(tmp_path)

    assert len(manifest_rows(tmp_path, "catalogue", "a")) == 1


def test_no_zip_says_so(tmp_path, capsys):
    best_of.run(tmp_path)

    assert "Aucun zip" in capsys.readouterr().out
