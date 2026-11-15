from types import SimpleNamespace

import numpy as np
import pytest

from pipeline.explanations import known_pairs


# Faux modèle : l'empreinte ne regarde que le quart en haut à gauche (et, avec le miroir, en haut à droite)
def fake_embedder():
    torch = pytest.importorskip("torch")
    from torch import nn

    class TopLeft(nn.Module):
        def __init__(self):
            super().__init__()
            torch.manual_seed(0)
            self.conv = nn.Conv2d(3, 4, 1)

        def forward(self, x):
            return self.conv(x)[..., :8, :8].mean(dim=(2, 3))

    preprocessing = lambda image: torch.from_numpy(np.array(image)).permute(2, 0, 1).float() / 255  # noqa: E731
    return SimpleNamespace(network=TopLeft().eval(), device="cpu", preprocessing=preprocessing)


def photo(seed):
    from PIL import Image

    return Image.fromarray(np.random.default_rng(seed).integers(0, 255, (16, 16, 3), dtype=np.uint8))


def test_occlusion_points_at_the_squares_the_model_looks_at():
    embedder = fake_embedder()
    from dorsalmatch import explain

    x, y = explain.to_tensor(embedder, photo(0)), explain.to_tensor(embedder, photo(1))
    heat = explain.occlusion(embedder, x, explain.embed(embedder, y)[0], grid=2)
    assert heat[0].min() > 0
    assert heat[1].max() == 0


def test_grad_cam_is_a_positive_map_of_the_last_feature_map():
    embedder = fake_embedder()
    from dorsalmatch import explain

    x, y = explain.to_tensor(embedder, photo(0)), explain.to_tensor(embedder, photo(1))
    heat = explain.grad_cam(embedder, x, explain.embed(embedder, y)[0])
    assert heat.shape == (16, 16)
    assert heat.min() >= 0


def test_deletion_curve_goes_from_the_score_to_everything_hidden():
    embedder = fake_embedder()
    from dorsalmatch import explain

    x, y = explain.to_tensor(embedder, photo(0)), explain.to_tensor(embedder, photo(1))
    reference = explain.embed(embedder, y)[0]
    curve = explain.deletion_curve(embedder, x, reference, np.ones((2, 2)), grid=4, steps=4)
    assert curve["carte"][0] == pytest.approx(float(explain.embed(embedder, x)[0] @ reference), abs=1e-5)
    assert curve["carte"][-1] == pytest.approx(curve["hasard"][-1], abs=1e-5)


def test_reciprocal_matches_of_a_photo_with_itself_link_each_zone_to_itself():
    embedder = fake_embedder()
    from dorsalmatch import explain

    x = explain.to_tensor(embedder, photo(0))
    matches = explain.reciprocal_matches(embedder, x, x, links=10)
    assert len(matches) == 10
    assert all(a == b for a, b, _ in matches)


def test_explain_returns_images_and_curve():
    embedder = fake_embedder()
    from dorsalmatch import explain

    result = explain.explain(embedder, photo(0), photo(1), "gradcam")
    assert result["requete"].size == (16, 16)
    assert result["aire_carte"] <= 1


def test_explain_reciprocal_gives_only_the_links():
    embedder = fake_embedder()
    from dorsalmatch import explain

    result = explain.explain(embedder, photo(0), photo(1), "reciprocal")
    assert set(result) == {"cosinus", "liens"}


def test_known_pairs_are_two_photos_of_the_same_dolphin_and_side():
    photos = [{"individu": individual, "cote": side, "fichier_origine": f"{individual}{side}{number}.jpg"}
              for individual in ("a", "b") for side in ("D", "G") for number in range(3)]
    photos.append({"individu": "c", "cote": "D", "fichier_origine": "seule.jpg"})

    pairs = known_pairs(photos, count=10)
    assert len(pairs) == 4  # c n'a qu'une photo
    assert all(a["individu"] == b["individu"] and a["cote"] == b["cote"] and a is not b for a, b in pairs)
    assert pairs == known_pairs(photos, count=10)
