from __future__ import annotations

import timm
import torch
from torch import nn

from dorsalmatch.models.common import IMAGENET, preprocessing

# CONSTANTES
WEIGHTS = "hf-hub:BVRA/MegaDescriptor-L-384"

# Normalisation ImageNet, celle de l'entraînement (wildlife-tools) et du config.json
# du hub, pas le 0.5/0.5 de la fiche Hugging Face. Résultats quasi identiques.
PREPROCESSING = preprocessing(384, *IMAGENET)


# Swin-L de MegaDescriptor ; pas de GeM ni de neck : timm fait le pooling moyen
class MegaDescriptor(nn.Module):
    # Cartes de Swin en (N, H, W, C) : voir explain.channels_first
    channels_last = True

    def __init__(self):
        super().__init__()
        # pretrained=True : les poids viennent directement du hub
        self.backbone = timm.create_model(WEIGHTS, pretrained=True, num_classes=0)

    def forward(self, images: torch.Tensor) -> torch.Tensor:
        return self.backbone(images)
