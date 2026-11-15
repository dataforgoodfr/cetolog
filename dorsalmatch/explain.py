from __future__ import annotations

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image, ImageDraw

# CONSTANTES
GRID = 8  # occlusion : carrés par côté de la photo
DELETION_GRID = 16  # courbe de suppression : carrés par côté
DELETION_STEPS = 10
LINKS = 20  # zones réciproques affichées
FOCUS = 0.75  # zones réciproques : seul le quart le plus activé de chaque photo, sinon l'eau se relie à l'eau
HEIGHT = 400  # hauteur des images côte à côte


# Photo -> tenseur prétraité (1, 3, S, S)
def to_tensor(embedder, image: Image.Image) -> torch.Tensor:
    return embedder.preprocessing(image.convert("RGB")).unsqueeze(0).to(embedder.device)


# Empreintes comme Embedder.embed : moyenne de la photo et de son miroir
@torch.no_grad()
def embed(embedder, tensors: torch.Tensor) -> torch.Tensor:
    plain = F.normalize(embedder.network(tensors).float(), dim=1)
    mirrored = F.normalize(embedder.network(tensors.flip(-1)).float(), dim=1)
    return F.normalize(plain + mirrored, dim=1)


# Cosinus avec reference quand chaque masque (grille de 0 et 1) est mis à zéro, c'est-à-dire au gris moyen
def masked_cosines(embedder, x, masks: torch.Tensor, reference: torch.Tensor, batch_size: int = 8) -> torch.Tensor:
    cosines = []
    for start in range(0, len(masks), batch_size):
        hidden = F.interpolate(masks[start:start + batch_size, None].float(), size=x.shape[-2:], mode="nearest")
        cosines.append(embed(embedder, x * (1 - hidden)) @ reference)
    return torch.cat(cosines)


# 1. Occlusion : la baisse du cosinus quand on cache chaque carré, en lots
def occlusion(embedder, x, reference, grid: int = GRID) -> np.ndarray:
    one_square_each = torch.eye(grid * grid, device=x.device).reshape(-1, grid, grid)
    nothing = torch.zeros(1, grid, grid, device=x.device)
    drop = masked_cosines(embedder, x, nothing, reference) - masked_cosines(embedder, x, one_square_each, reference)
    return drop.clamp(min=0).reshape(grid, grid).cpu().numpy()


# La dernière carte de caractéristiques (1, C, h, w) du réseau, avant le pooling, et l'empreinte
def last_feature_map(network, x) -> tuple[torch.Tensor, torch.Tensor]:
    found = {}

    def keep(_module, _inputs, output):
        if isinstance(output, torch.Tensor) and output.dim() == 4:
            found["map"] = output

    hooks = [module.register_forward_hook(keep) for module in network.modules()]
    try:
        embedding = network(x)
    finally:
        for hook in hooks:
            hook.remove()
    return embedding, found["map"]


# 2. Grad-CAM : les zones dont le gradient fait monter le cosinus, en un seul passage
def grad_cam(embedder, x, reference) -> np.ndarray:
    with torch.enable_grad():
        embedding, feature_map = last_feature_map(embedder.network, x)
        cosine = F.normalize(embedding.float(), dim=1)[0] @ reference
        (gradient,) = torch.autograd.grad(cosine, feature_map)
    weights = gradient.mean(dim=(2, 3), keepdim=True)
    return F.relu((weights * feature_map).sum(dim=1))[0].detach().float().cpu().numpy()


METHODS = {"occlusion": occlusion, "gradcam": grad_cam}


# 3. Courbe de suppression : le cosinus quand on cache les zones les plus importantes d'abord, puis au hasard
# Une carte fidèle fait chuter le cosinus plus vite que le hasard
def deletion_curve(embedder, x, reference, heatmap: np.ndarray, grid: int = DELETION_GRID,
                   steps: int = DELETION_STEPS, seed: int = 0) -> dict[str, np.ndarray]:
    squares = F.interpolate(torch.as_tensor(heatmap)[None, None].float(), size=(grid, grid), mode="area").flatten()
    orders = {"carte": squares.argsort(descending=True),
              "hasard": torch.randperm(grid * grid, generator=torch.Generator().manual_seed(seed))}
    fractions = np.linspace(0, 1, steps + 1)

    curves = {"fraction": fractions}
    for name, order in orders.items():
        masks = torch.zeros(steps + 1, grid * grid)
        for step, fraction in enumerate(fractions):
            masks[step, order[:round(fraction * grid * grid)]] = 1
        curves[name] = masked_cosines(embedder, x, masks.reshape(-1, grid, grid).to(x.device), reference).cpu().numpy()
    return curves


# 4. Zones réciproques : chaque zone de a et sa plus proche dans b, gardée si b la désigne en retour
@torch.no_grad()
def reciprocal_matches(embedder, x, y, links: int = LINKS) -> list[tuple[tuple[float, float], tuple[float, float], float]]:
    maps = [last_feature_map(embedder.network, tensor)[1][0] for tensor in (x, y)]
    (height_a, width_a), (height_b, width_b) = (feature_map.shape[-2:] for feature_map in maps)
    a, b = (feature_map.flatten(1).T.float() for feature_map in maps)  # (zones, C)
    kept_a, kept_b = (zones.norm(dim=1) >= zones.norm(dim=1).quantile(FOCUS) for zones in (a, b))

    similarity = F.normalize(a, dim=1) @ F.normalize(b, dim=1).T
    similarity[~kept_a] = -2
    similarity[:, ~kept_b] = -2
    best_in_b, best_in_a = similarity.argmax(dim=1), similarity.argmax(dim=0)
    mutual = ((best_in_a[best_in_b] == torch.arange(len(a), device=a.device)) & kept_a).nonzero().flatten()
    mutual = mutual[similarity[mutual, best_in_b[mutual]].argsort(descending=True)][:links]

    # Centre de chaque zone, en fraction de la largeur et de la hauteur
    def center(index: int, height: int, width: int) -> tuple[float, float]:
        return ((index % width + 0.5) / width, (index // width + 0.5) / height)

    return [(center(int(i), height_a, width_a), center(int(best_in_b[i]), height_b, width_b), float(similarity[i, best_in_b[i]]))
            for i in mutual]


# Carte superposée à la photo : rouge = compte beaucoup
def overlay(image: Image.Image, heatmap: np.ndarray, alpha: float = 0.6) -> Image.Image:
    image = image.convert("RGB")
    heat = np.asarray(heatmap, dtype=float)
    heat = heat / heat.max() if heat.max() > 0 else heat
    heat = np.asarray(Image.fromarray(np.uint8(255 * heat)).resize(image.size, Image.BILINEAR)) / 255
    red = np.zeros((*heat.shape, 3))
    red[..., 0] = 255
    weight = alpha * heat[..., None]
    return Image.fromarray(np.uint8(np.asarray(image) * (1 - weight) + red * weight))


# Les photos à la même hauteur, côte à côte
def side_by_side(images: list[Image.Image], height: int = HEIGHT) -> Image.Image:
    resized = [image.convert("RGB").resize((round(image.width * height / image.height), height)) for image in images]
    canvas = Image.new("RGB", (sum(image.width for image in resized), height), "white")
    left = 0
    for image in resized:
        canvas.paste(image, (left, 0))
        left += image.width
    return canvas


# Les liens réciproques tracés entre les deux photos
def draw_links(a: Image.Image, b: Image.Image, matches, height: int = HEIGHT) -> Image.Image:
    canvas = side_by_side([a, b], height)
    width_a = round(a.width * height / a.height)
    width_b = canvas.width - width_a
    draw = ImageDraw.Draw(canvas)
    for (xa, ya), (xb, yb), _ in matches:
        start, end = (xa * width_a, ya * height), (width_a + xb * width_b, yb * height)
        draw.line([start, end], fill=(0, 220, 120), width=2)
        for x, y in (start, end):
            draw.ellipse([x - 4, y - 4, x + 4, y + 4], outline=(0, 220, 120), width=2)
    return canvas


# Tout pour une paire : liens réciproques, cartes des deux photos (sauf method="reciprocal"),
# et si demandé la courbe de suppression (la plus lente)
def explain(embedder, query: Image.Image, candidate: Image.Image, method: str = "occlusion", curve: bool = True) -> dict:
    x, y = to_tensor(embedder, query), to_tensor(embedder, candidate)
    query_embedding, candidate_embedding = embed(embedder, torch.cat([x, y]))
    result = {
        "cosinus": float(query_embedding @ candidate_embedding),
        "liens": draw_links(query, candidate, reciprocal_matches(embedder, x, y)),
    }
    if method == "reciprocal":
        return result

    query_map = METHODS[method](embedder, x, candidate_embedding)
    result["requete"] = overlay(query, query_map)
    result["candidat"] = overlay(candidate, METHODS[method](embedder, y, query_embedding))
    if curve:
        points = deletion_curve(embedder, x, candidate_embedding, query_map)
        # Aire sous la courbe : plus elle est basse par rapport au hasard, plus la carte est fidèle
        result.update(suppression=points, aire_carte=float(points["carte"].mean()), aire_hasard=float(points["hasard"].mean()))
    return result
