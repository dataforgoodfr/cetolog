import numpy as np
import torch
from lightglue import ALIKED, LightGlue
from lightglue.utils import numpy_image_to_torch
from PIL import Image


class LocalMatcher:
    def __init__(self, max_keypoints=2048, max_side=1024, device=None):
        # CUDA préférable
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.max_side = max_side
        self.extractor = ALIKED(max_num_keypoints=max_keypoints).eval().to(self.device)
        self.matcher = LightGlue(features="aliked").eval().to(self.device)
        self._cache = {}

    def features(self, path):
        path = str(path)
        if path not in self._cache:
            image = Image.open(path).convert("RGB")
            image.thumbnail((self.max_side, self.max_side))
            tensor = numpy_image_to_torch(np.asarray(image)).to(self.device)
            with torch.no_grad():
                self._cache[path] = self.extractor.extract(tensor)
        return self._cache[path]

    def count_matches(self, path_a, path_b):
        with torch.no_grad():
            out = self.matcher(
                {"image0": self.features(path_a), "image1": self.features(path_b)}
            )
        return len(out["matches"][0])


def local_score(matcher, query_path, side, individual, catalogue, catalogue_path):
    return max(
        (
            matcher.count_matches(query_path, catalogue_path(p))
            for p in catalogue
            if p["individu"] == individual and p["cote"] == side
        ),
        default=0,
    )


def rerank(result, matcher, history, catalogue, query_path, catalogue_path, k=10):
    query = history[result["lines"][0]]
    path = query_path(query)
    top = result["candidats"][:k]
    scores = [
        local_score(
            matcher, path, query["cote"], c["individu"], catalogue, catalogue_path
        )
        for c in top
    ]
    order = np.argsort(scores, kind="stable")[::-1]
    ranked = [{**top[i], "matches": scores[i]} for i in order]
    labels = [c["individu"] for c in ranked]
    rank = (
        labels.index(result["individu"]) + 1 if result["individu"] in labels else None
    )
    return {**result, "candidats": ranked, "rang": rank, "rang_avant": result["rang"]}


def rerank_all(results, matcher, history, catalogue, query_path, catalogue_path, k=10):
    return [
        rerank(r, matcher, history, catalogue, query_path, catalogue_path, k)
        for r in results
    ]


def rank_changes(reranked):
    pairs = [
        (r["rang"], r["rang_avant"]) for r in reranked if r["rang"] and r["rang_avant"]
    ]
    new, old = np.array(pairs).T
    return {
        "mieux": int(np.sum(new < old)),
        "egal": int(np.sum(new == old)),
        "moins_bien": int(np.sum(new > old)),
    }
