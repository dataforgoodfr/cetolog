from __future__ import annotations

import timm
import torch
from huggingface_hub import hf_hub_download
from torch import nn

from dorsalmatch.models.common import IMAGENET, GeM, preprocessing

# CONSTANTES
WEIGHTS = ("Saving-Willy/cetacean-classifier", "last.ckpt")  # model.safetensors : neck non entraîné
PREPROCESSING = preprocessing(768, *IMAGENET) # Process l'image en fonction des images d'entraînement


# EfficientNetV2-M de Happywhale ; noms des attributs = ceux du checkpoint
class CetaceaNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.backbone = timm.create_model(
            "tf_efficientnetv2_m", pretrained=False, num_classes=0,
            features_only=True, out_indices=(3, 4),
        )
        self.global_pools = nn.ModuleList([GeM(), GeM()])
        self.neck = nn.BatchNorm1d(sum(self.backbone.feature_info.channels()))

        # weights_only=False : checkpoint Lightning (pickle)
        checkpoint = torch.load(hf_hub_download(*WEIGHTS), map_location="cpu", weights_only=False)
        weights = {key.removeprefix("model."): value for key, value in checkpoint["state_dict"].items()}
        missing, _ = self.load_state_dict(weights, strict=False)
        if missing:
            raise RuntimeError(f"Poids absents du checkpoint : {missing[:8]}")

    def forward(self, images: torch.Tensor) -> torch.Tensor:
        feature_maps = self.backbone(images)
        pooled = [pool(feature_map) for feature_map, pool in zip(feature_maps, self.global_pools)]
        return self.neck(torch.cat(pooled, dim=1))
