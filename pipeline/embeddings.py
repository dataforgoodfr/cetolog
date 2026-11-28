from __future__ import annotations

import argparse
import csv
from functools import partial
from pathlib import Path

import numpy as np

# CONSTANTES
DATA = Path("data")
KINDS = ("catalogue", "historique", "best_of")
MODELS = ["cetaceanet"]
COLUMNS = ["livraison", "individu", "cote", "fichier_origine", "sha256"]
DETOURE = "_detoure"  # suffixe des empreintes de photos détourées
CHUNK = 32  # photos détourées en mémoire à la fois
BOX_MARGIN = 0.10  # marge autour du dauphin, en fraction de son grand côté


# 1. Les photos du manifeste présentes dans curated/
def read_photos(manifest: Path, kind: str, data: Path) -> list[dict]:
    with open(manifest, encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    photos_folder = data / "curated" / kind / "photos" / manifest.stem
    kept = []
    for row in rows:
        path = photos_folder / row["individu"] / row["fichier_origine"]
        if path.exists():
            kept.append({**row, "chemin": path})
        else:
            print(f"  photo manquante, ignorée : {path}")

    return kept


# 2. Les empreintes d'une livraison
def embed_delivery(embedder, model: str, manifest: Path, kind: str, data: Path) -> None:
    output = data / "derived" / "embeddings" / kind / manifest.stem
    embeddings_file = output / f"{model}.npy"
    if embeddings_file.exists():
        print(f"{kind}/{manifest.stem} : {model} déjà calculé")
        return

    rows = read_photos(manifest, kind, data)
    print(f"{kind}/{manifest.stem} : {len(rows)} photos avec {model}", flush=True)
    embeddings = embedder.embed([row["chemin"] for row in rows])

    # Empreintes en dernier : un calcul coupé est refait
    output.mkdir(parents=True, exist_ok=True)
    with open(output / "photos.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    np.save(embeddings_file, embeddings)


# 2 bis. Recadrer sur le dauphin en gardant la mer
# Le masque sert seulement à trouver le dauphin. Le cadre est carré pour que
# l'Embedder ne déforme pas la dorsale, et coupé s'il dépasse de la photo.
def crop_keep_sea(segmenter, image, margin: float = BOX_MARGIN, square: bool = True):
    from PIL import Image

    if not isinstance(image, Image.Image):
        image = Image.open(image)
    image = image.convert("RGB")
    rows, cols = np.nonzero(np.asarray(segmenter.mask(image)) == 255)
    if rows.size == 0:  # masque vide
        return image
    return image.crop(
        sea_box(
            (cols.min(), rows.min(), cols.max() + 1, rows.max() + 1),
            image.size,
            margin,
            square,
        )
    )


# Rectangle du dauphin (gauche, haut, droite, bas) -> cadre élargi dans la photo
def sea_box(box, size, margin: float, square: bool) -> tuple[int, int, int, int]:
    left, top, right, bottom = box
    width, height = right - left, bottom - top
    pad = margin * max(width, height)
    sides = [width + 2 * pad, height + 2 * pad]
    if square:
        sides = [max(sides)] * 2
    centres = [(left + right) / 2, (top + bottom) / 2]
    edges = []
    for side, centre, limit in zip(sides, centres, size, strict=True):
        side = min(side, limit)
        start = min(max(centre - side / 2, 0), limit - side)
        edges.append((round(start), round(start + side)))
    (left, right), (top, bottom) = edges
    return left, top, right, bottom


# 2 ter. Les empreintes des photos préparées (détourées, recadrées)
# Chaque photo est préparée une fois pour tous les modèles. Les lignes suivent
# photos.csv : <modèle><suffixe>.npy se lit avec le même photos.csv
def embed_delivery_detoured(
    embedders: dict,
    prepare,
    manifest: Path,
    kind: str,
    data: Path,
    suffix: str = DETOURE,
) -> None:
    output = data / "derived" / "embeddings" / kind / manifest.stem
    todo = {
        model: embedder
        for model, embedder in embedders.items()
        if not (output / f"{model}{suffix}.npy").exists()
    }
    if not todo:
        print(f"{kind}/{manifest.stem} : détourées déjà calculées")
        return

    rows = read_photos(manifest, kind, data)
    listed = output / "photos.csv"
    if listed.exists():
        with open(listed, encoding="utf-8") as file:
            expected = [row["fichier_origine"] for row in csv.DictReader(file)]
        if expected != [row["fichier_origine"] for row in rows]:
            raise RuntimeError(
                f"{listed} ne suit pas le manifeste : recalculer d'abord les "
                "empreintes des photos brutes"
            )
    print(
        f"{kind}/{manifest.stem} : {len(rows)} photos détourées avec {', '.join(todo)}",
        flush=True,
    )
    parts = {model: [] for model in todo}
    for start in range(0, len(rows), CHUNK):
        images = [prepare(row["chemin"]) for row in rows[start : start + CHUNK]]
        for model, embedder in todo.items():
            parts[model].append(embedder.embed(images))
        print(f"  {min(start + CHUNK, len(rows))}/{len(rows)}", flush=True)

    output.mkdir(parents=True, exist_ok=True)
    if not listed.exists():
        with open(listed, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=COLUMNS, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
    for model, embeddings in parts.items():
        np.save(output / f"{model}{suffix}.npy", np.vstack(embeddings))


# 3. Toutes les livraisons, modèle par modèle
def run(
    models: list[str] = MODELS,
    data: Path = DATA,
    kinds: tuple[str, ...] = KINDS,
    detoure: bool = False,
    segmenter_config: dict | None = None,
    suffix: str = DETOURE,
    keep_sea: bool = False,
) -> None:
    from dorsalmatch import Embedder

    if detoure:
        from dorsalmatch import Segmenter

        embedders = {model: Embedder(model) for model in models}
        segmenter = Segmenter(segmenter_config)
        prepare = (
            partial(crop_keep_sea, segmenter)
            if keep_sea
            else segmenter.remove_background
        )
        for kind in kinds:
            for manifest in sorted(
                (data / "curated" / kind / "manifests").glob("*.csv")
            ):
                embed_delivery_detoured(
                    embedders, prepare, manifest, kind, data, suffix
                )
        return

    for model in models:
        embedder = Embedder(model)
        for kind in kinds:
            for manifest in sorted(
                (data / "curated" / kind / "manifests").glob("*.csv")
            ):
                embed_delivery(embedder, model, manifest, kind, data)


# 4. La ligne de commande
def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Calcule les empreintes des photos, modèle par modèle."
    )
    parser.add_argument(
        "models",
        nargs="*",
        default=MODELS,
        help=f"modèles à utiliser (défaut : {' '.join(MODELS)})",
    )
    parser.add_argument(
        "--kinds",
        nargs="+",
        default=KINDS,
        choices=KINDS,
        help=f"types de livraison à traiter (défaut : {' '.join(KINDS)})",
    )
    parser.add_argument(
        "--data", type=Path, default=DATA, help=f"dossier des données (défaut : {DATA})"
    )
    parser.add_argument(
        "--detoure",
        action="store_true",
        help="détourer les photos avec le Segmenter avant les empreintes "
        f"(<modèle>{DETOURE}.npy)",
    )
    parser.add_argument(
        "--segmenter",
        nargs="+",
        default=[],
        metavar="CLÉ=VALEUR",
        help="réglages du Segmenter à remplacer, ex. crop=false",
    )
    parser.add_argument(
        "--mer",
        action="store_true",
        help="avec --detoure : recadrer sur le dauphin sans retirer la mer",
    )
    parser.add_argument(
        "--suffixe",
        default=DETOURE,
        help=f"suffixe des fichiers détourés (défaut : {DETOURE})",
    )
    return parser.parse_args(argv)


# crop=false threshold=0.5 -> {"crop": False, "threshold": 0.5}
def segmenter_settings(pairs: list[str]) -> dict | None:
    import yaml

    settings = {}
    for pair in pairs:
        key, separator, value = pair.partition("=")
        if not separator:
            raise SystemExit(f"--segmenter attend CLÉ=VALEUR, pas {pair!r}")
        settings[key] = yaml.safe_load(value)
    return settings or None


# uv run --group ml python -m pipeline.embeddings
# uv run --group ml python -m pipeline.embeddings miewid --kinds catalogue historique
# uv run --group ml python -m pipeline.embeddings cetaceanet miewid --detoure
# ... --detoure --segmenter crop=false --suffixe _fond_blanc
# ... --detoure --mer --suffixe _recadre_mer
if __name__ == "__main__":
    args = parse_args()
    run(
        args.models,
        data=args.data,
        kinds=tuple(args.kinds),
        detoure=args.detoure,
        segmenter_config=segmenter_settings(args.segmenter),
        suffix=args.suffixe,
        keep_sea=args.mer,
    )
