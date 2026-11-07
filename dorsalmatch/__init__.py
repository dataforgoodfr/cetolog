from dorsalmatch.match import evaluate, neighbors, pairs, search

__all__ = ["MODELS", "Embedder", "evaluate", "neighbors", "pairs", "search"]


# PyTorch chargé seulement à la première utilisation d'Embedder ou MODELS
def __getattr__(name: str):
    if name == "Embedder":
        from dorsalmatch.embedder import Embedder

        return Embedder
    if name == "MODELS":
        from dorsalmatch.models import MODELS

        return MODELS
    raise AttributeError(f"module 'dorsalmatch' has no attribute {name!r}")
