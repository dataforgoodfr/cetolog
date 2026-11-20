import numpy as np
import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("timm")
pytest.importorskip("yaml")

from PIL import Image  # noqa: E402

from dorsalmatch import segmenter  # noqa: E402
from dorsalmatch.segmenter import Segmenter, load_config, resolve_weights  # noqa: E402


# Faux réseau : la carte choisie couvre la moitié gauche, les 6 autres la droite
def fake_segmenter(**config):
    fake = Segmenter.__new__(Segmenter)
    fake.config = load_config({"input_size": 4, "mask_resample": "nearest", **config})
    fake.device = "cpu"

    def network(x):
        left = torch.zeros(1, 1, 4, 4)
        left[..., :2] = 1
        return tuple(
            left if i == fake.config["output_index"] else 1 - left for i in range(7)
        )

    fake.network = network
    return fake


def red_photo():
    return Image.new("RGB", (8, 4), (200, 0, 0))


def test_defaults_match_the_notebook():
    config = load_config()
    assert config["output_index"] == 4  # la « d5 » du notebook
    assert config["threshold"] == 0.3
    assert config["input_size"] == 320


def test_unknown_parameter_is_refused():
    with pytest.raises(ValueError, match="Paramètres inconnus"):
        load_config({"treshold": 0.5})


def test_mask_uses_the_configured_output():
    mask = np.asarray(fake_segmenter().mask(red_photo()))
    assert mask.shape == (4, 8)
    assert (mask[:, :4] == 255).all()
    assert (mask[:, 4:] == 0).all()


def test_threshold_above_the_map_keeps_nothing():
    mask = np.asarray(fake_segmenter(threshold=1.0).mask(red_photo()))
    assert (mask == 0).all()


def test_remove_background_crops_to_the_object():
    result = fake_segmenter().remove_background(red_photo())
    assert result.size == (4, 4)
    assert (np.asarray(result) == (200, 0, 0)).all()


def test_remove_background_without_crop_whitens_the_rest():
    pixels = np.asarray(fake_segmenter(crop=False).remove_background(red_photo()))
    assert pixels.shape == (4, 8, 3)
    assert (pixels[:, 4:] == 255).all()


def test_nothing_salient_returns_the_photo():
    photo = red_photo()
    result = fake_segmenter(threshold=1.0).remove_background(photo)
    assert result.size == photo.size


def test_weights_from_a_local_path(tmp_path):
    assert resolve_weights({"path": str(tmp_path / "u2net.pth")}) == (
        tmp_path / "u2net.pth"
    )


def test_weights_from_hugging_face(monkeypatch):
    calls = []
    huggingface_hub = pytest.importorskip("huggingface_hub")
    monkeypatch.setattr(
        huggingface_hub,
        "hf_hub_download",
        lambda *args, **kwargs: calls.append((args, kwargs)) or "/cache/u2net.pth",
    )
    path = resolve_weights(
        {"repo": "org/u2net", "filename": "u2net.pth", "revision": "abc"}
    )
    assert str(path) == "/cache/u2net.pth"
    assert calls == [(("org/u2net", "u2net.pth"), {"revision": "abc"})]


@pytest.mark.parametrize("weights", [{}, {"path": "a.pth", "repo": "org/u2net"}])
def test_weights_need_exactly_one_source(weights):
    with pytest.raises(ValueError, match="soit path, soit repo"):
        resolve_weights(weights)


# Les clés des poids sont les noms des attributs du code vendorisé
@pytest.mark.parametrize(("name", "keys"), [("u2net", 798), ("u2netp", 798)])
def test_vendored_networks_have_the_weight_layout(name, keys):
    state = segmenter.NETWORKS[name](3, 1).state_dict()
    assert len(state) == keys
    assert "stage1.rebnconvin.conv_s1.weight" in state
    assert "outconv.weight" in state
