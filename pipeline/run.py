from __future__ import annotations

from pathlib import Path

from pipeline import embeddings, propositions
from pipeline.photos import best_of

# Chaque best-of cherché dans le catalogue (lancer bootstrap avant)

# CONSTANTES
DATA = Path("data")


# Dernière version du catalogue avec ses empreintes
def latest_catalogue(data: Path) -> str:
    folder = data / "derived" / "embeddings" / "catalogue"
    versions = sorted(version.name for version in folder.glob("*") if version.is_dir()) if folder.exists() else []
    if not versions:
        raise RuntimeError(f"Pas de catalogue dans {folder} : lancer d'abord python -m pipeline.bootstrap")
    return versions[-1]


def run(data: Path = DATA) -> None:
    catalogue = latest_catalogue(data)

    best_of.run(data)
    embeddings.run(data=data, kinds=("best_of",))

    for delivery in sorted((data / "derived" / "embeddings" / "best_of").glob("*")):
        output = data / "derived" / "propositions" / f"{delivery.name}.csv"
        if output.exists():
            print(f"{delivery.name} : propositions déjà faites")
            continue
        print(f"{delivery.name} : propositions dans {propositions.write(delivery.name, catalogue, data)}")


# uv run --group ml python -m pipeline.run
if __name__ == "__main__":
    run()
