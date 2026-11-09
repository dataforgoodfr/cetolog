from __future__ import annotations

import os

# GPU Apple : repli sur le CPU pour les opérations manquantes
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import torch  # noqa: E402
import torch.nn.functional as F  # noqa: E402
from PIL import Image  # noqa: E402

from dorsalmatch.models import MODELS  # noqa: E402


# Le GPU Apple si possible, sinon CUDA, sinon le CPU
def pick_device() -> str:
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


# Embedder("cetaceanet").embed(["a.jpg", "b.jpg"])
class Embedder:
    def __init__(self, name: str = "cetaceanet"):
        if name not in MODELS:
            raise ValueError(f"Modèle inconnu : {name}. Modèles disponibles : {', '.join(MODELS)}")
        build_network, self.preprocessing = MODELS[name]
        self.name = name
        self.device = pick_device()
        self.network = build_network().to(self.device).eval()

    # Vecteurs de norme 1 : cosinus = produit scalaire
    @torch.no_grad()
    def embed(self, images: list[str | Path | Image.Image], batch_size: int = 8) -> np.ndarray:
        batches = []
        for start in range(0, len(images), batch_size):
            # Sans rotation EXIF
            opened = [image if isinstance(image, Image.Image) else Image.open(image) for image in images[start:start + batch_size]]
            tensors = torch.stack([self.preprocessing(image.convert("RGB")) for image in opened]).to(self.device)            
            # UPDATE : Moyenne de la photo et de son miroir
            plain = F.normalize(self.network(tensors).float(), dim=1)
            mirrored = F.normalize(self.network(tensors.flip(-1)).float(), dim=1)
            batches.append(F.normalize(plain + mirrored, dim=1).cpu())

        return torch.cat(batches).numpy()
