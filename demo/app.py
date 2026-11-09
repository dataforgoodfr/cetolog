from __future__ import annotations

import os
import tempfile
from pathlib import Path

# Avant l'import de Gradio : tout reste dans un dossier effacé à l'arrêt
WORKSPACE = tempfile.TemporaryDirectory(prefix="cetolog-")
os.environ["GRADIO_TEMP_DIR"] = WORKSPACE.name

import gradio as gr  # noqa: E402
from PIL import Image  # noqa: E402

from demo.propositions import catalogue_photos, latest, load, propose  # noqa: E402
from pipeline.storage import connect  # noqa: E402

# Tout vient du bucket : les empreintes au démarrage, chaque photo à l'affichage
CACHE = Path(WORKSPACE.name) / "data"
BUCKET = connect()
for kind in ("catalogue", "best_of"):
    BUCKET.pull(CACHE, prefix=f"derived/embeddings/{kind}/")
    if not (CACHE / "derived" / "embeddings" / kind).exists():
        raise SystemExit(f"Le bucket {BUCKET.name} n'a pas d'empreintes pour {kind} (derived/embeddings/{kind}/) : "
                         "les y déposer avant de relancer la démo")


def fetch(path: str) -> str:
    return str(BUCKET.fetch(path, CACHE))


# CONSTANTES
SHOWN = 10
BEST_OF = latest("best_of", CACHE)
CATALOGUE = latest("catalogue", CACHE)
PROPOSITIONS = propose(BEST_OF, CATALOGUE, CACHE)
CATALOGUE_PHOTOS = catalogue_photos(load("catalogue", CATALOGUE, CACHE)[0])
SIDES = {"D": "droite", "G": "gauche"}
# Sans la photo au nom illisible : elle n'a pas de côté, ce n'est pas un dauphin
DOLPHINS_LIST = sorted({name for name, side in CATALOGUE_PHOTOS if side in SIDES})
DOLPHINS = len(DOLPHINS_LIST)
PAGE = 12
PAGES = (len(DOLPHINS_LIST) + PAGE - 1) // PAGE

# Case grise : pas de photo pour ce côté
MISSING = Path(WORKSPACE.name) / "pas_de_photo.png"
Image.new("RGB", (400, 260), (225, 225, 225)).save(MISSING)


# 1. Un individu choisi : ses photos, droites d'abord
def individual_photos(individual: str) -> list[tuple[str, str]]:
    photos = sorted(PROPOSITIONS[individual]["photos"], key=lambda photo: photo["cote"])
    return [(fetch(photo["chemin"]), SIDES.get(photo["cote"], "?")) for photo in photos]


# 2. Ses candidats, droite puis gauche
def candidate_photos(individual: str) -> list[tuple[str, str]]:
    images = []
    for rank, candidate in enumerate(PROPOSITIONS[individual]["candidats"][:SHOWN], start=1):
        for side, side_name in SIDES.items():
            path = CATALOGUE_PHOTOS.get((candidate["individu"], side))
            score = f"{candidate[side]:.2f}" if side in candidate else "–"
            name = f"{rank}. {candidate['individu']} · score {candidate['score']:.2f}"
            images.append((fetch(path), f"{name} · {side_name} {score}") if path else (str(MISSING), f"{name} · pas de photo {side_name}"))
    return images


# 3. Le catalogue, page par page
def catalogue_page(page: int) -> tuple[list[tuple[str, str]], str, int]:
    page = max(1, min(int(page), PAGES))
    images = []
    for name in DOLPHINS_LIST[(page - 1) * PAGE:page * PAGE]:
        for side, side_name in SIDES.items():
            path = CATALOGUE_PHOTOS.get((name, side))
            images.append((fetch(path), f"{name} · {side_name}") if path else (str(MISSING), f"{name} · pas de photo {side_name}"))
    return images, f"Page {page} / {PAGES}", page


def show(individual: str):
    return individual_photos(individual), candidate_photos(individual)


with gr.Blocks(title="Cétolog · démo", analytics_enabled=False) as demo:
    gr.Markdown(f"# Cétolog · best-of ➜ catalogue\n"
                f"Chaque individu provisoire du best-of `{BEST_OF}` ({len(PROPOSITIONS)} individus) "
                f"est cherché par CetaceaNet dans le catalogue `{CATALOGUE}` ({DOLPHINS} dauphins).")

    first = next(iter(PROPOSITIONS))
    with gr.Row():
        with gr.Column(scale=2):
            individual = gr.Dropdown(list(PROPOSITIONS), value=first, label="Individu provisoire")
            photos = gr.Gallery(individual_photos(first), label="Ses photos dans le best-of", columns=3, height=520,
                                object_fit="contain")
        with gr.Column(scale=3):
            candidates = gr.Gallery(candidate_photos(first), label=f"Les {SHOWN} dauphins du catalogue les plus ressemblants",
                                    columns=2, height=900, object_fit="contain")
            gr.Markdown("**Score** : le cosinus entre les empreintes des dorsales, moyenné sur les côtés en commun. "
                        "Plus il est proche de 1, plus les dorsales se ressemblent.")

    with gr.Accordion(f"Parcourir le catalogue ({DOLPHINS} dauphins)", open=False):
        page = gr.State(1)
        with gr.Row():
            previous = gr.Button("Précédent")
            position = gr.Markdown(f"Page 1 / {PAGES}")
            following = gr.Button("Suivant")
        browser = gr.Gallery(label="Catalogue", columns=4, height=900, object_fit="contain")

    individual.change(show, individual, [photos, candidates])
    demo.load(catalogue_page, page, [browser, position, page])
    previous.click(lambda current: catalogue_page(current - 1), page, [browser, position, page])
    following.click(lambda current: catalogue_page(current + 1), page, [browser, position, page])


# Mot de passe si DEMO_PASSWORD est défini
def credentials() -> tuple[str, str] | None:
    password = os.environ.get("DEMO_PASSWORD")
    return (os.environ.get("DEMO_USER", "miraceti"), password) if password else None


# uv run --group demo python -m demo.app
if __name__ == "__main__":
    demo.launch(allowed_paths=[WORKSPACE.name], auth=credentials())
