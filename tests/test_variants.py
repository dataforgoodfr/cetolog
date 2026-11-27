from pathlib import Path

from review.variants import LOST, WON, effect, image_path, slice_name


def test_effect():
    assert effect(3, 1) == WON
    assert effect(None, 1) == WON
    assert effect(1, 2) == LOST
    assert effect(1, None) == LOST
    assert effect(5, 2) == "monte"
    assert effect(2, None) == "descend"
    assert effect(1, 1) == "pareil"
    assert effect(None, None) == "pareil"


def test_slice_and_image_names():
    assert slice_name("requete", "") == "requete_brut"
    assert slice_name("bon", "_fond_blanc_marge3") == "bon_marge3"
    photo = {"sha256": "ab" * 32}
    assert image_path(Path("d"), "_recadre_mer", photo) == Path(
        "d/derived/variantes/mer/abababababababab.jpg"
    )
