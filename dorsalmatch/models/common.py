from __future__ import annotations

from collections.abc import Callable

import torch
from PIL import Image
from torch import nn
from torchvision import transforms as T

# CONSTANTES
IMAGENET = ((0.485, 0.456, 0.406), (0.229, 0.224, 0.225))
INCEPTION = ((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))  # couleurs de 0-255 à -1..1


# Photo en carré, sans recadrage, normalisée
def preprocessing(
    size: int,
    mean: tuple,
    std: tuple,
    interpolation: T.InterpolationMode = T.InterpolationMode.BICUBIC,
) -> Callable[[Image.Image], torch.Tensor]:
    return T.Compose(
        [
            T.Resize((size, size), interpolation=interpolation),
            T.ToTensor(),
            T.Normalize(mean, std),
        ]
    )


# GeM pooling
class GeM(nn.Module):
    def __init__(self, p: float = 3.0, eps: float = 1e-6):
        super().__init__()
        self.p = nn.Parameter(torch.ones(1) * p)
        self.eps = eps

    def forward(self, feature_map: torch.Tensor) -> torch.Tensor:
        return (
            feature_map.clamp(min=self.eps)
            .pow(self.p)
            .mean(dim=(-2, -1))
            .pow(1.0 / self.p)
        )
