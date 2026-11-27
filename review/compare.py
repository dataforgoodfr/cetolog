"""Comparaison des modèles dans FiftyOne, photo par photo.

Même classement que `notebooks/baseline_ml.ipynb`. Une tranche par photo :

- `requete` : la photo d'historique, avec le rang et les scores de chaque modèle,
  et ses cartes Grad-CAM contre le bon dauphin et contre le premier faux ;
- `bon` : le bon dauphin au catalogue, même côté ;
- `faux_<modèle>` : le premier faux candidat du modèle.

Les cartes viennent de `python -m review.heatmaps` ; une carte absente n'est pas
affichée.

    uv run --group review python -m review.compare
"""

from __future__ import annotations

import argparse
import os
from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pandas as pd

from demo.propositions import SIDES, TOP, rank
from pipeline.similarities import findable
from review.ranking import CATALOGUE_DELIVERY, HISTORY_DELIVERIES, ranking_outcome

# CONSTANTES
DATA = Path(__file__).resolve().parents[1] / "data"
MODELS = ("cetaceanet", "miewid", "megadescriptor")
REFERENCE = MODELS[0]  # choisit les photos mises de côté (Step 2.1)
DATASET = "cetolog_comparaison"
HEATMAPS = Path("derived") / "explications" / "gradcam"
QUERY, MATCH = "requete", "bon"
HEATMAP_SIZE = 256  # taille des cartes affichées
MASKS = Path("derived") / "masques"
TAGS_BACKUP = Path("derived") / "explications" / "tags_comparaison.json"


def false_slice(model: str) -> str:
    return f"faux_{model}"


# Les photos d'une livraison et les empreintes d'un modèle
def load(kind: str, delivery: str, model: str, data: Path = DATA):
    folder = data / "derived" / "embeddings" / kind / delivery
    photos = pd.read_csv(folder / "photos.csv", dtype=str, keep_default_na=False)
    photos["chemin"] = [
        str(data / "curated" / kind / "photos" / delivery / individual / name)
        for individual, name in zip(
            photos["individu"], photos["fichier_origine"], strict=True
        )
    ]
    return photos.to_dict("records"), np.load(folder / f"{model}.npy")


def load_history(model: str, data: Path, deliveries: Sequence[str]):
    photos, embeddings = [], []
    for delivery in deliveries:
        delivery_photos, delivery_embeddings = load("historique", delivery, model, data)
        photos += [{**photo, "livraison": delivery} for photo in delivery_photos]
        embeddings.append(delivery_embeddings)
    return photos, np.vstack(embeddings)


# La photo de catalogue d'un dauphin pour un côté
def catalogue_index(catalogue: list[dict]) -> dict[tuple[str, str], dict]:
    return {(photo["individu"], photo["cote"]): photo for photo in catalogue}


# Le côté le mieux noté d'un candidat
def best_side(candidate: dict) -> str:
    return max((side for side in SIDES if side in candidate), key=candidate.get)


def score_models(
    data: Path = DATA,
    models: Sequence[str] = MODELS,
    deliveries: Sequence[str] = HISTORY_DELIVERIES,
    catalogue_delivery: str = CATALOGUE_DELIVERY,
) -> list[dict]:
    """Une entrée par photo d'historique notée, avec le résultat de chaque modèle.

    Returns
    -------
    list[dict]
        `photo` (la requête), `bon` (photo du catalogue du bon dauphin, même
        côté), puis pour chaque modèle un dict : `rang`, `cas`, `score_bon`,
        `score_faux` et `faux` (photo du premier faux candidat, son meilleur
        côté).
    """
    history, reference = load_history(REFERENCE, data, deliveries)
    catalogue, catalogue_reference = load(
        "catalogue", catalogue_delivery, REFERENCE, data
    )
    lines = [
        line
        for line, photo in enumerate(history)
        if findable(photo, reference[line], catalogue, catalogue_reference)
    ]
    by_side = catalogue_index(catalogue)
    entries = [
        {
            "photo": history[line],
            "bon": by_side[(history[line]["individu"], history[line]["cote"])],
        }
        for line in lines
    ]

    for model in models:
        _, embeddings = load_history(model, data, deliveries)
        _, catalogue_embeddings = load("catalogue", catalogue_delivery, model, data)
        for entry, line in zip(entries, lines, strict=True):
            individual = entry["photo"]["individu"]
            candidates, _ = rank(
                [entry["photo"]],
                embeddings[line : line + 1],
                catalogue,
                catalogue_embeddings,
            )
            names = [candidate["individu"] for candidate in candidates]
            position = names.index(individual) if individual in names else None
            first_false = next(c for c in candidates if c["individu"] != individual)
            entry[model] = {
                "rang": position + 1 if position is not None else None,
                "cas": str(
                    ranking_outcome(position + 1 if position is not None else None)
                ),
                "score_bon": candidates[position]["score"]
                if position is not None
                else None,
                "score_faux": first_false["score"],
                "faux": by_side[(first_false["individu"], best_side(first_false))],
            }
    return entries


# Clé de cache d'une carte : la photo expliquée, contre la photo de référence
def heatmap_path(data: Path, model: str, photo: dict, reference: dict) -> Path:
    return (
        data
        / HEATMAPS
        / model
        / f"{photo['sha256'][:16]}_vs_{reference['sha256'][:16]}.npy"
    )


def load_heat(data: Path, model: str, photo: dict, reference: dict):
    path = heatmap_path(data, model, photo, reference)
    if not path.exists():
        return None
    return np.load(path).astype(np.float32)


def read_heatmap(data: Path, model: str, photo: dict, reference: dict):
    import fiftyone as fo
    from PIL import Image

    heat = load_heat(data, model, photo, reference)
    if heat is None:
        return None
    heat = heat / heat.max() if heat.max() > 0 else heat
    # La carte couvre toute la photo : FiftyOne l'étire à sa taille
    smooth = Image.fromarray(np.uint8(255 * heat)).resize(
        (HEATMAP_SIZE, HEATMAP_SIZE), Image.BILINEAR
    )
    return fo.Heatmap(map=np.asarray(smooth), range=[0, 255])


# Masque du dauphin (U-2-Net), calculé par `python -m review.masks`
def mask_path(data: Path, photo: dict) -> Path:
    return data / MASKS / f"{photo['sha256'][:16]}.png"


def load_mask(data: Path, photo: dict):
    from PIL import Image

    path = mask_path(data, photo)
    if not path.exists():
        return None
    return np.asarray(Image.open(path)) > 127


def dolphin_share(heat, mask) -> float | None:
    """Part de la carte sur le dauphin ÷ part de la photo qu'il occupe.

    1 = hasard ; au-dessus, le modèle regarde le dauphin ; en dessous, l'eau.
    """
    from PIL import Image

    if heat is None or mask is None or heat.sum() <= 0 or not mask.any():
        return None
    # Carte étirée à la taille du masque
    heat = np.asarray(
        Image.fromarray(heat.astype(np.float32), mode="F").resize(
            (mask.shape[1], mask.shape[0]), Image.BILINEAR
        )
    ).clip(min=0)
    if heat.sum() <= 0:
        return None
    return float(heat[mask].sum() / heat.sum() / mask.mean())


# Tags gardés d'une reconstruction à l'autre : (requête, tranche) -> tags
def save_tags(data: Path) -> dict[tuple[str, str], list[str]]:
    import json

    import fiftyone as fo

    if not fo.dataset_exists(DATASET):
        return {}
    dataset = fo.load_dataset(DATASET)
    query_of_group = dict(
        zip(
            *dataset.select_group_slices(QUERY).values(["group.id", "filepath"]),
            strict=True,
        )
    )
    tags = {}
    for name in dataset.group_slices:
        view = dataset.select_group_slices(name)
        for group_id, sample_tags in zip(
            *view.values(["group.id", "tags"]), strict=True
        ):
            if sample_tags and group_id in query_of_group:
                tags[(query_of_group[group_id], name)] = sample_tags
    if tags:
        backup = data / TAGS_BACKUP
        backup.parent.mkdir(parents=True, exist_ok=True)
        backup.write_text(
            json.dumps(
                [
                    {"requete": query, "tranche": name, "tags": sample_tags}
                    for (query, name), sample_tags in tags.items()
                ],
                ensure_ascii=False,
                indent=1,
            ),
            encoding="utf-8",
        )
    return tags


def build(entries: Sequence[dict], data: Path = DATA, models: Sequence[str] = MODELS):
    """Construit le dataset groupé et ses vues."""
    import fiftyone as fo
    from fiftyone import ViewField as F

    tags = save_tags(data)
    if fo.dataset_exists(DATASET):
        fo.delete_dataset(DATASET)
    dataset = fo.Dataset(DATASET)
    dataset.persistent = True
    dataset.add_group_field("group", default=QUERY)

    def media(photo: dict) -> str:
        return str(Path(photo["chemin"]).resolve())

    def label(text: str) -> fo.Classification:
        return fo.Classification(label=text)

    def add_mask(sample: fo.Sample, photo: dict) -> None:
        mask = load_mask(data, photo)
        if mask is not None:
            sample["dauphin"] = fo.Segmentation(mask=mask.astype(np.uint8))

    def restore_tags(sample: fo.Sample, query_path: str, name: str) -> None:
        sample.tags = list(tags.get((query_path, name), []))

    samples = []
    found = missing = 0
    for entry in entries:
        group = fo.Group()
        photo, match = entry["photo"], entry["bon"]
        query = fo.Sample(filepath=media(photo), group=group.element(QUERY))
        query["individual"] = photo["individu"]
        query["side"] = photo["cote"]
        query["delivery"] = photo["livraison"]
        query["models_rank1"] = sum(entry[m]["rang"] == 1 for m in models)
        query["label_individual"] = label(f"{photo['individu']} · {photo['cote']}")
        match_sample = fo.Sample(filepath=media(match), group=group.element(MATCH))
        match_sample["individual"] = match["individu"]
        match_sample["side"] = match["cote"]
        match_sample["label_individual"] = label(
            f"{match['individu']} · {match['cote']}"
        )
        match_sample["label_is_match"] = label("bon dauphin")
        add_mask(query, photo)
        add_mask(match_sample, match)
        restore_tags(query, query.filepath, QUERY)
        restore_tags(match_sample, query.filepath, MATCH)
        group_samples = [query, match_sample]

        for model in models:
            result = entry[model]
            query[f"{model}_rank"] = result["rang"]
            query[f"{model}_outcome"] = result["cas"]
            query[f"{model}_score_bon"] = result["score_bon"]
            query[f"{model}_score_faux"] = result["score_faux"]
            query[f"{model}_faux"] = result["faux"]["individu"]
            match_sample[f"{model}_score"] = result["score_bon"]
            query[f"label_{model}"] = label(
                f"{model} : rang {result['rang']} · {result['score_bon']:.2f}"
            )
            match_sample[f"label_{model}"] = label(
                f"{model} : {result['score_bon']:.2f}"
            )

            false = result["faux"]
            false_sample = fo.Sample(
                filepath=media(false), group=group.element(false_slice(model))
            )
            false_sample["individual"] = false["individu"]
            false_sample["side"] = false["cote"]
            false_sample[f"{model}_score"] = result["score_faux"]
            false_sample["label_individual"] = label(
                f"{false['individu']} · {false['cote']}"
            )
            false_sample[f"label_{model}"] = label(
                f"{model} : 1er faux · {result['score_faux']:.2f}"
            )
            add_mask(false_sample, false)
            restore_tags(false_sample, query.filepath, false_slice(model))
            group_samples.append(false_sample)

            for sample, explained, reference, field, share_field in (
                (
                    query,
                    photo,
                    match,
                    f"gradcam_{model}_bon",
                    f"{model}_part_dauphin_bon",
                ),
                (
                    query,
                    photo,
                    false,
                    f"gradcam_{model}_faux",
                    f"{model}_part_dauphin_faux",
                ),
                (match_sample, match, photo, f"gradcam_{model}", None),
                (false_sample, false, photo, f"gradcam_{model}", None),
            ):
                heatmap = read_heatmap(data, model, explained, reference)
                if heatmap is None:
                    missing += 1
                    continue
                sample[field] = heatmap
                found += 1
                share = dolphin_share(
                    load_heat(data, model, explained, reference),
                    load_mask(data, explained),
                )
                sample[share_field or f"{model}_part_dauphin"] = share
        samples += group_samples

    dataset.add_samples(samples)
    dataset.mask_targets = {"dauphin": {1: "dauphin"}}
    dataset.save()
    print(f"{len(entries)} photos, cartes Grad-CAM : {found} lues, {missing} absentes")
    print(f"tags remis : {sum(len(t) for t in tags.values())}")

    # Vues : les désaccords entre modèles
    hors_top = f"hors top {TOP}"
    views = {
        "tous rang 1": F("models_rank1") == len(models),
        f"tous {hors_top}": F("models_rank1") == 0,
    }
    for model in models:
        if model == REFERENCE:
            continue
        views[f"{REFERENCE} rang 1, {model} {hors_top}"] = (
            F(f"{REFERENCE}_rank") == 1
        ) & (F(f"{model}_outcome") == hors_top)
        views[f"{model} rang 1, {REFERENCE} non"] = (F(f"{model}_rank") == 1) & (
            F(f"{REFERENCE}_rank") != 1
        )
    for name, expression in views.items():
        dataset.save_view(name, dataset.match(expression))
    return dataset


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data", type=Path, default=DATA)
    parser.add_argument(
        "--no-launch", action="store_true", help="construire sans ouvrir l'app"
    )
    args = parser.parse_args()

    os.environ["FIFTYONE_DO_NOT_TRACK"] = "1"  # avant l'import de FiftyOne
    import fiftyone as fo

    dataset = build(score_models(args.data), args.data)
    if not args.no_launch:
        fo.launch_app(dataset).wait()


if __name__ == "__main__":
    main()
