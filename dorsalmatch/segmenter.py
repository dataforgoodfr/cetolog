from __future__ import annotations

import math
import warnings
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
import yaml
from PIL import Image

from dorsalmatch.embedder import pick_device
from dorsalmatch.models.u2net import U2NET, U2NETP

# CONSTANTES
DEFAULT_CONFIG = Path(__file__).with_name("segmenter.yaml")
NETWORKS = {"u2net": U2NET, "u2netp": U2NETP}
RESAMPLE = {
    "nearest": Image.Resampling.NEAREST,
    "bilinear": Image.Resampling.BILINEAR,
    "bicubic": Image.Resampling.BICUBIC,
}


# Les valeurs par défaut, remplacées par celles du fichier ou du dict donné
def load_config(config: str | Path | dict | None = None) -> dict:
    defaults = yaml.safe_load(DEFAULT_CONFIG.read_text())
    if config is None:
        return defaults
    if not isinstance(config, dict):
        config = yaml.safe_load(Path(config).read_text())
    unknown = set(config) - set(defaults)
    if unknown:
        raise ValueError(f"Paramètres inconnus : {', '.join(sorted(unknown))}")
    return defaults | config


# Chemin local ou dépôt Hugging Face, jamais les deux
def resolve_weights(weights: dict) -> Path:
    if ("path" in weights) == ("repo" in weights):
        raise ValueError("weights : donner soit path, soit repo (+ filename)")
    if "path" in weights:
        return Path(weights["path"]).expanduser()
    from huggingface_hub import hf_hub_download

    return Path(
        hf_hub_download(
            weights["repo"], weights["filename"], revision=weights.get("revision")
        )
    )


def load_weights(path: Path) -> dict:
    if path.suffix == ".safetensors":
        from safetensors.torch import load_file

        return load_file(path, device="cpu")
    return torch.load(path, map_location="cpu", weights_only=True)


# Segmenter().remove_background("a.jpg") : la nageoire sur fond blanc, recadrée
class Segmenter:
    def __init__(self, config: str | Path | dict | None = None):
        self.config = load_config(config)
        self.device = pick_device()
        network = NETWORKS[self.config["model"]](3, 1)
        network.load_state_dict(load_weights(resolve_weights(self.config["weights"])))
        self.network = network.to(self.device).eval()

    def preprocess(self, image: Image.Image) -> torch.Tensor:
        size = self.config["input_size"]
        # Bilinéaire, comme le RescaleT de U-2-Net (skimage, ordre 1)
        resized = image.resize((size, size), resample=Image.Resampling.BILINEAR)
        pixels = np.asarray(resized, dtype=np.float32)
        # Division par le maximum de la photo, comme le ToTensorLab de U-2-Net
        pixels /= max(pixels.max(), 1e-8)
        normalisation = self.config["normalisation"]
        pixels = (pixels - np.array(normalisation["mean"])) / np.array(
            normalisation["std"]
        )
        return torch.from_numpy(pixels.transpose(2, 0, 1)).float()[None]

    # Masque en niveaux de gris à la taille de la photo : 255 = objet, 0 = fond
    @torch.no_grad()
    def mask(self, image: str | Path | Image.Image) -> Image.Image:
        image = _open(image)
        with warnings.catch_warnings():
            # F.upsample du code amont, déprécié dans PyTorch
            warnings.simplefilter("ignore", UserWarning)
            outputs = self.network(self.preprocess(image).to(self.device))
        saliency = outputs[self.config["output_index"]][0, 0]
        saliency = (saliency - saliency.min()) / (saliency.max() - saliency.min())
        binary = (saliency > self.config["threshold"]).cpu().numpy()
        mask = Image.fromarray(binary.astype(np.uint8) * 255).resize(
            image.size, resample=RESAMPLE[self.config["mask_resample"]]
        )
        # Marge à pleine résolution : même largeur dans tous les sens
        return _dilate(mask, round(self.config["margin"] * max(image.size)))

    def remove_background(self, image: str | Path | Image.Image) -> Image.Image:
        image = _open(image)
        mask = self.mask(image)
        background = Image.new("RGB", image.size, tuple(self.config["background"]))
        result = Image.composite(image, background, mask)
        if not self.config["crop"]:
            return result
        rows, cols = np.nonzero(np.asarray(mask) == 255)
        # Rien de saillant : la photo telle quelle
        if rows.size == 0:
            return image
        return result.crop((cols.min(), rows.min(), cols.max() + 1, rows.max() + 1))


# Filtre max carré. Calculé sur le masque réduit d'un facteur radius // 8 :
# 100 fois plus rapide sur une grande photo, marge dépassée d'au plus 1/8.
def _dilate(mask: Image.Image, radius: int) -> Image.Image:
    if radius <= 0:
        return mask
    pixels = torch.from_numpy(np.asarray(mask, dtype=np.float32))[None, None]
    height, width = pixels.shape[-2:]
    scale = max(1, radius // 8)
    small = F.max_pool2d(pixels, scale, scale, ceil_mode=True)
    size = 2 * math.ceil(radius / scale) + 1
    for kernel in ((size, 1), (1, size)):
        small = F.max_pool2d(small, kernel, 1, (kernel[0] // 2, kernel[1] // 2))
    large = small.repeat_interleave(scale, -2).repeat_interleave(scale, -1)
    return Image.fromarray(large[0, 0, :height, :width].numpy().astype(np.uint8))


def _open(image: str | Path | Image.Image) -> Image.Image:
    if not isinstance(image, Image.Image):
        image = Image.open(image)
    return image.convert("RGB")
