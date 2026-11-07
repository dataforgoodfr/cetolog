# Ajouter un modèle : un fichier ici, puis une ligne dans MODELS
from dorsalmatch.models import cetaceanet

MODELS = {  # nom : (réseau, prétraitement attendu par ses poids)
    "cetaceanet": (cetaceanet.CetaceaNet, cetaceanet.PREPROCESSING),
}
