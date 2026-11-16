from __future__ import annotations

import importlib.util
from functools import cache

import gradio as gr
import pandas as pd
from PIL import Image

from demo.propositions import MODEL

# CONSTANTES
METHODS = {
    "Occlusion : la plus fiable (environ 5 min sur CPU)": "occlusion",
    "Grad-CAM : rapide (moins d'une minute)": "gradcam",
    "Zones réciproques : les zones qui se ressemblent d'une photo à l'autre (quelques secondes)": "reciprocal",
}
OTHER_SIDE = {"D": "G", "G": "D"}
# Sans PyTorch (image Docker de la démo), le panneau dit comment l'obtenir
READY = importlib.util.find_spec("torch") is not None


# Le modèle, chargé à la première explication seulement
@cache
def embedder():
    from dorsalmatch import Embedder

    return Embedder(MODEL)


def photo_choices(propositions: dict, individual: str) -> list[tuple[str, int]]:
    return [(f"{number + 1}. côté {photo['cote'] or '?'} · {photo['fichier_origine']}", number)
            for number, photo in enumerate(propositions[individual]["photos"])]


def candidate_choices(propositions: dict, individual: str, shown: int) -> list[tuple[str, int]]:
    return [(f"{rank}. {candidate['individu']} · score {candidate['score']:.2f}", rank - 1)
            for rank, candidate in enumerate(propositions[individual]["candidats"][:shown], start=1)]


# Le panneau sous le matching, qui suit l'individu choisi en haut de la démo
def panel(individual: gr.Dropdown, propositions: dict, catalogue_photos: dict, fetch, shown: int) -> None:
    gr.Markdown("## Explicabilité du matching\nQuelles zones des photos expliquent qu'un candidat ressemble à l'individu ?")
    if not READY:
        gr.Markdown("Il faut PyTorch : relancer avec `uv run --group demo --group ml python -m demo.app`")
        return

    first = individual.value
    with gr.Row():
        photo = gr.Dropdown(photo_choices(propositions, first), value=0, label="Photo de l'individu")
        candidate = gr.Dropdown(candidate_choices(propositions, first, shown), value=0, label="Candidat à expliquer")
    method = gr.Radio(list(METHODS), value=list(METHODS)[1], label="Technique d'explicabilité")
    with_curve = gr.Checkbox(False, label="Valider la carte par une courbe de suppression (environ 1 min de plus sur CPU, "
                                          "sauf zones réciproques)")
    button = gr.Button("Générer l'explicabilité", variant="primary")

    summary = gr.Markdown()
    with gr.Row():
        query_map = gr.Image(label="Photo de l'individu : en rouge, ce qui fait le score", type="pil", visible=False)
        candidate_map = gr.Image(label="Photo du candidat : en rouge, ce qui fait le score", type="pil", visible=False)
    links = gr.Image(label="Zones réciproques : chaque zone désigne l'autre comme la plus ressemblante", type="pil",
                     visible=False)
    curve = gr.LinePlot(x="fraction cachée", y="cosinus", color="ordre", visible=False,
                        label="Courbe de suppression : la carte doit faire chuter le cosinus plus vite que le hasard")

    def run(individual: str, photo: int, rank: int, method: str, with_curve: bool):
        query = propositions[individual]["photos"][int(photo)]
        name = propositions[individual]["candidats"][int(rank)]["individu"]
        side = query["cote"] if (name, query["cote"]) in catalogue_photos else OTHER_SIDE.get(query["cote"], "D")
        path = catalogue_photos.get((name, side))
        if path is None:
            raise gr.Error(f"Pas de photo de {name} au catalogue")

        from dorsalmatch.explain import explain

        technique = METHODS[method]
        with_curve = with_curve and technique != "reciprocal"
        result = explain(embedder(), Image.open(fetch(query["chemin"])), Image.open(fetch(path)), technique, with_curve)

        text = f"**{individual}** ➜ **{name}** (côté {side}) · cosinus entre ces deux photos **{result['cosinus']:.2f}**"
        table = None
        if with_curve:
            points = result["suppression"]
            table = pd.DataFrame([{"fraction cachée": fraction, "cosinus": float(points[order][step]), "ordre": order}
                                  for order in ("carte", "hasard") for step, fraction in enumerate(points["fraction"])])
            text += (f" · aire sous la courbe : carte **{result['aire_carte']:.2f}**, hasard {result['aire_hasard']:.2f} "
                     "(plus basse que le hasard : la carte est fidèle)")

        has_maps = technique != "reciprocal"
        return (text,
                gr.Image(result.get("requete"), visible=has_maps),
                gr.Image(result.get("candidat"), visible=has_maps),
                gr.Image(result["liens"], visible=not has_maps),
                gr.LinePlot(table, visible=with_curve))

    def follow(name: str):
        return (gr.Dropdown(choices=photo_choices(propositions, name), value=0),
                gr.Dropdown(choices=candidate_choices(propositions, name, shown), value=0))

    individual.change(follow, individual, [photo, candidate])
    button.click(run, [individual, photo, candidate, method, with_curve], [summary, query_map, candidate_map, links, curve])
