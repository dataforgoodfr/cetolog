import hashlib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

# Fichiers copiés tels quels d'un autre dépôt : chemin, empreinte SHA-256.
# Ne changer l'empreinte que pour une nouvelle copie depuis l'amont.
VENDORED = {
    "dorsalmatch/models/u2net.py": (
        "f8608362f680739bbd16c17498f5d214e438de78dc162228fee0e556451d1949"
    ),
}


@pytest.mark.parametrize(("path", "expected"), VENDORED.items())
def test_vendored_file_is_unchanged(path, expected):
    digest = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
    assert digest == expected, (
        f"{path} est vendorisé et ne doit pas être modifié (voir son en-tête). "
        "Les noms des attributs sont les clés des poids."
    )
