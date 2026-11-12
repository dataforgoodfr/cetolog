from __future__ import annotations

import timm
import torch
from huggingface_hub import hf_hub_download
from safetensors.torch import load_file
from torch import nn
from torchvision import transforms as T

from dorsalmatch.models.common import IMAGENET, GeM, preprocessing

# CONSTANTES
WEIGHTS = ("conservationxlabs/miewid-msv3", "model.safetensors")

PREPROCESSING = preprocessing(
    440, *IMAGENET, interpolation=T.InterpolationMode.BILINEAR
)  # redimensionnement bilinéaire ; celui de cetaceanet : bicubique


# EfficientNetV2-RW-M de MiewID ; noms des attributs = ceux du checkpoint
class MiewID(nn.Module):
    def __init__(self):
        super().__init__()
        # pretrained=False : le checkpoint remplace les poids ImageNet
        self.backbone = timm.create_model(
            "efficientnetv2_rw_m", pretrained=False, num_classes=0
        )
        self.backbone.global_pool = GeM()
        self.bn = nn.BatchNorm1d(self.backbone.num_features)

        # final.* : la tête de classification, inutile pour une empreinte
        checkpoint = load_file(hf_hub_download(*WEIGHTS), device="cpu")
        weights = {
            key: value
            for key, value in checkpoint.items()
            if not key.startswith("final.")
        }
        missing, unexpected = self.load_state_dict(weights, strict=False)
        if missing or unexpected:
            raise RuntimeError(
                f"Poids inattendus : absents {missing[:8]}, en trop {unexpected[:8]}"
            )

    def forward(self, images: torch.Tensor) -> torch.Tensor:
        return self.bn(self.backbone(images).flatten(1))
