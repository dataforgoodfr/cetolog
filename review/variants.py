"""Les variantes de détourage de `baseline_ml_v2` dans FiftyOne.

Une tranche par variante pour la requête (`requete_<variante>`) et le bon
dauphin (`bon_<variante>`). Sur chaque photo : le rang de chaque modèle et
l'effet de la variante par rapport à la photo brute.

Les photos préparées sont enregistrées dans `data/derived/variantes/`.

    uv run --group ml --group review python -m review.variants
"""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Sequence
from pathlib import Path

import numpy as np

from review.compare import DATA, MODELS, load_mask, score_models

# CONSTANTES
DATASET = "cetolog_detourage"
# Suffixe des empreintes -> (nom court, nom affiché)
VARIANTS = {
    "": ("brut", "brut"),
    "_detoure": ("detoure", "détouré recadré"),
    "_fond_blanc": ("fond_blanc", "fond blanc, sans recadrage"),
    "_fond_blanc_marge3": ("marge3", "fond blanc, marge 3 %"),
    "_recadre_mer": ("mer", "recadré, mer gardée"),
}
QUERY, MATCH = "requete", "bon"
IMAGES = Path("derived") / "variantes"
IMAGE_SIZE = 1024  # grand côté des photos enregistrées
TAGS_BACKUP = Path("derived") / "explications" / "tags_detourage.json"
WON, LOST = "gagne le rang 1", "perd le rang 1"


def slice_name(role: str, suffix: str) -> str:
    return f"{role}_{VARIANTS[suffix][0]}"


# Effet d'une variante sur le rang du bon dauphin (None : hors classement)
def effect(raw_rank: int | None, rank: int | None) -> str:
    raw, new = raw_rank or 10_000, rank or 10_000
    if raw != 1 and new == 1:
        return WON
    if raw == 1 and new != 1:
        return LOST
    if new < raw:
        return "monte"
    if new > raw:
        return "descend"
    return "pareil"


def image_path(data: Path, suffix: str, photo: dict) -> Path:
    return data / IMAGES / VARIANTS[suffix][0] / f"{photo['sha256'][:16]}.jpg"


# La préparation de chaque variante, comme dans le notebook V2
def preparations() -> dict:
    from dorsalmatch import Segmenter
    from pipeline.embeddings import crop_keep_sea

    segmenter = Segmenter()
    return {
        "_detoure": segmenter.remove_background,
        "_fond_blanc": Segmenter({"crop": False}).remove_background,
        "_fond_blanc_marge3": Segmenter(
            {"crop": False, "margin": 0.03}
        ).remove_background,
        "_recadre_mer": lambda image: crop_keep_sea(segmenter, image),
    }


# Photos réduites avant préparation : les marges sont relatives, le rendu est le même
def render_images(entries: Sequence[dict], data: Path) -> None:
    from PIL import Image

    photos = {}
    for entry in entries:
        for photo in (entry["photo"], entry["bon"]):
            photos[photo["sha256"]] = photo
    todo = [
        (suffix, photo)
        for suffix in VARIANTS
        if suffix
        for photo in photos.values()
        if not image_path(data, suffix, photo).exists()
    ]
    if not todo:
        return
    print(f"{len(todo)} photos à préparer", flush=True)
    prepare = preparations()
    for done, (suffix, photo) in enumerate(todo, 1):
        image = Image.open(photo["chemin"]).convert("RGB")
        image.thumbnail((IMAGE_SIZE, IMAGE_SIZE))
        path = image_path(data, suffix, photo)
        path.parent.mkdir(parents=True, exist_ok=True)
        prepare[suffix](image).save(path, quality=90)
        if done % 200 == 0:
            print(f"  {done}/{len(todo)}", flush=True)


# Tags gardés d'une reconstruction à l'autre : (requête, tranche) -> tags
def save_tags(data: Path) -> dict[tuple[str, str], list[str]]:
    import fiftyone as fo

    if not fo.dataset_exists(DATASET):
        return {}
    dataset = fo.load_dataset(DATASET)
    raw_query = dataset.select_group_slices(slice_name(QUERY, ""))
    query_of_group = dict(zip(*raw_query.values(["group.id", "filepath"]), strict=True))
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
    dataset.add_group_field("group", default=slice_name(QUERY, ""))

    samples = []
    for entry in entries:
        photo, match = entry["photo"], entry["bon"]
        query_path = str(Path(photo["chemin"]).resolve())
        # Mêmes champs sur toutes les tranches, pour filtrer depuis chacune
        fields = {
            "individual": photo["individu"],
            "side": photo["cote"],
            "delivery": photo["livraison"],
        }
        for model in models:
            raw_rank = entry[model]["rang"]
            for suffix, (short, _) in VARIANTS.items():
                rank = entry[model + suffix]["rang"]
                fields[f"{model}_rang_{short}"] = rank
                if suffix:
                    fields[f"{model}_effet_{short}"] = effect(raw_rank, rank)

        group = fo.Group()
        for suffix, (short, readable) in VARIANTS.items():
            for role, shown in ((QUERY, photo), (MATCH, match)):
                name = slice_name(role, suffix)
                path = (
                    Path(shown["chemin"]).resolve()
                    if not suffix
                    else image_path(data, suffix, shown).resolve()
                )
                sample = fo.Sample(filepath=str(path), group=group.element(name))
                sample.update_fields(fields)
                sample.tags = list(tags.get((query_path, name), []))
                sample["label_variante"] = fo.Classification(label=readable)
                if role == MATCH:
                    sample["label_bon"] = fo.Classification(label="bon dauphin")
                for model in models:
                    rank = entry[model + suffix]["rang"]
                    text = f"{model} : rang {rank if rank else 'hors classement'}"
                    if suffix:
                        text += f" · {fields[f'{model}_effet_{short}']}"
                    sample[f"label_{model}"] = fo.Classification(label=text)
                # Masque U-2-Net sur la photo brute
                if not suffix:
                    mask = load_mask(data, shown)
                    if mask is not None:
                        sample["dauphin"] = fo.Segmentation(mask=mask.astype(np.uint8))
                samples.append(sample)

    dataset.add_samples(samples)
    dataset.mask_targets = {"dauphin": {1: "dauphin"}}
    dataset.save()
    print(f"{len(entries)} photos, {len(VARIANTS)} variantes")
    print(f"tags remis : {sum(len(t) for t in tags.values())}")

    # Vues : photos qui gagnent ou perdent le rang 1
    for model in models:
        for suffix, (short, readable) in VARIANTS.items():
            if not suffix:
                continue
            for outcome in (LOST, WON):
                view = dataset.match(F(f"{model}_effet_{short}") == outcome)
                dataset.save_view(f"{model} · {readable} · {outcome}", view)
    return dataset


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data", type=Path, default=DATA)
    parser.add_argument(
        "--no-launch", action="store_true", help="construire sans ouvrir l'app"
    )
    args = parser.parse_args()

    entries = score_models(
        args.data, [model + suffix for model in MODELS for suffix in VARIANTS]
    )
    render_images(entries, args.data)

    os.environ["FIFTYONE_DO_NOT_TRACK"] = "1"  # avant l'import de FiftyOne
    import fiftyone as fo

    dataset = build(entries, args.data)
    if not args.no_launch:
        fo.launch_app(dataset).wait()


if __name__ == "__main__":
    main()
