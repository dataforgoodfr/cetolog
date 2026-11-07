from __future__ import annotations

from pathlib import Path

from pipeline import embeddings
from pipeline.photos import catalogue

# À relancer seulement pour une nouvelle version du catalogue

# CONSTANTES
DATA = Path("data")


def run(data: Path = DATA) -> None:
    catalogue.run(data)
    embeddings.run(data=data, kinds=("catalogue",))


# uv run --group ml python -m pipeline.bootstrap
if __name__ == "__main__":
    run()
