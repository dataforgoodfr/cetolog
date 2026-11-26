# Spécifications — porter la démo Gradio dans le frontend Next.js

Ce document décrit **quoi** porter de [`demo/app.py`](../../demo/app.py) vers `frontend/`, avec quels contrats et quelles décisions à trancher. Il ne contient pas d’implémentation.

## 1. Objectif et non-objectifs

### Objectif

Reproduire dans `frontend/` le parcours principal de la démo Gradio, en conservant le principe **« le ML propose, Miraceti décide »** :

1. choisir un individu provisoire d’un best-of ;
2. voir ses photos, droite puis gauche ;
3. voir les 10 dauphins du catalogue les plus ressemblants, avec leur score ;
4. parcourir le catalogue page par page.

La démo Gradio reste la référence fonctionnelle tant que le port n’est pas validé. Les sorties et les scores doivent pouvoir être comparés à ceux de Python sur un jeu de test.

### Non-objectifs de la première version

- Enregistrer les décisions de Miraceti ou créer la base de données décrite dans [`bdd.md`](../cetolog_pipeline/bdd.md).
- Porter le panneau d’explicabilité (occlusion, Grad-CAM, zones réciproques, courbe de suppression) dès la première version.
- Réimplémenter CetaceaNet en JavaScript sans qu’un POC ONNX ait validé la faisabilité.
- Modifier `raw/`, écrire dans le bucket, ou versionner des photos ou des données privées.
- Remplacer les règles du dépôt : voir [`README.md#les-règles`](../../README.md#les-règles).

## 2. Parité fonctionnelle attendue

| Démo Gradio | Spécification frontend |
|---|---|
| `gr.Dropdown` « Individu provisoire » | Liste des individus du best-of, triée comme `by_number` (`IND2` avant `IND10`), avec le premier individu sélectionné par défaut. |
| `gr.Gallery` « Ses photos dans le best-of » | Photos de l’individu triées par `cote` : `""` d’abord (libellé `?`), puis `D`, puis `G`. Image grise de 400 × 260 si le côté manque. |
| `gr.Gallery` des 10 candidats | Deux vignettes par candidat (`D` puis `G`). Libellé : `rang. individu · score X.XX · côté Y Z.ZZ`, ou `pas de photo côté Y` si absent. |
| Markdown sur le score | Texte explicite : « meilleur cosinus entre les empreintes des dorsales, tous côtés confondus ». Préciser que ce n’est **pas une probabilité**. |
| `gr.Accordion` « Parcourir le catalogue » | Galerie paginée, 12 individus par page, 2 vignettes par individu, boutons Précédent/Suivant, position `Page n / N`. |
| `gr.State(1)` pour la page | Préférer un paramètre d’URL `?page=` pour rendre la page partageable et revenir dessus après rechargement. |
| `analytics_enabled=False` | Aucun analytics ajouté. |
| `DEMO_PASSWORD` / `DEMO_USER` | Authentification basique facultative, côté serveur uniquement. Sans `DEMO_PASSWORD`, la page reste ouverte, comme dans la démo. |

Note : `reponse` / `deja_au_catalogue` est calculé par `propose()` mais n’est pas affiché par la démo actuelle. Le contrat peut le transporter ; l’UI n’est pas tenue de l’afficher dans la première version.

### États à traiter

| État | Comportement attendu |
|---|---|
| Chargement initial | Afficher un état de chargement explicite, pas une page vide. |
| Bucket indisponible ou variables S3 absentes | Message d’erreur lisible, sans exposer le endpoint, le bucket ni les clés. |
| Aucune empreinte pour `catalogue` ou `best_of` | Message indiquant le préfixe `derived/embeddings/<jeu>/` manquant, comme la démo. |
| Individu sans photo exploitable (`cote` hors `D`/`G`) | Ignorer la photo pour le matching, comme `best_cosines`. |
| Candidat sans photo d’un côté | Vignette grise et libellé `pas de photo D/G`, pas d’erreur. |
| Aucun candidat | État vide explicite, pas un gallery vide muet. |
| Page demandée hors limites | Ramener à `1..N`, comme `catalogue_page`. |

## 3. Contrats de données

Les noms et les règles ci-dessous viennent de [`catalogue.md`](../miraceti_data/catalogue.md), [`propositions.py`](../../demo/propositions.py) et [`match.py`](../../dorsalmatch/match.py). Ce sont la source de vérité ; le frontend ne doit pas inventer son propre schéma.

### 3.1 Artefacts lus par la démo

```text
derived/embeddings/<jeu>/<livraison>/photos.csv
derived/embeddings/<jeu>/<livraison>/cetaceanet.npy
curated/<jeu>/photos/<livraison>/<individu>/<fichier_origine>
derived/propositions/<best_of>.csv
```

- `<jeu>` vaut `catalogue` ou `best_of`.
- `latest()` choisit le dossier dont le **nom** est maximal, sans parser la date.
- `photos.csv` contient au minimum `livraison`, `individu`, `cote`, `fichier_origine`, `sha256`. Un côté vide reste `""`, jamais `NaN`.
- `cetaceanet.npy` contient une empreinte de **688 nombres**, de norme 1. La ligne N correspond à la ligne N de `photos.csv`.
- Le cosinus est un produit scalaire entre empreintes normalisées.
- `derived/propositions/<best_of>.csv` contient 10 lignes par individu, avec `best_of`, `catalogue`, `individu`, `rang`, `candidat`, `score`, `cosinus_D`, `cosinus_G`, `deja_au_catalogue`.

### 3.2 Règles de calcul à préserver

Ces règles sont celles de `demo/propositions.py` et doivent servir de référence pour tout calcul côté serveur ou côté navigateur.

| Règle | Valeur / comportement |
|---|---|
| Côtés acceptés | `D` et `G` seulement. |
| Comparaison | Toutes les photos exploitables de l’individu (côté `D` ou `G`) sont comparées aux photos du catalogue du côté demandé. Le miroir sert uniquement au calcul de l’empreinte. |
| Score d’un candidat | `max(cosinus_D, cosinus_G)` pour ce dauphin. |
| Presque identique | Un cosinus `>= 0.97` est exclu des candidats et ajouté à `reponse`. |
| Classement | `(-score, individu)`, pour être stable d’un lancement à l’autre. |
| Nombre de candidats affichés | `10`. |
| Précision d’affichage | 2 décimales, comme la démo. Conserver la valeur complète dans le contrat interne. |
| Comparabilité du score | Comparer seulement les candidats d’un même individu : plus l’individu a de photos, plus le score peut monter. |
| Photos du catalogue | Première photo rencontrée pour chaque paire `(individu, cote)`. |
| Identifiants | `IND…` pour le best-of, `TUTR…` pour le catalogue. Ce ne sont pas des noms de personnes. |

### 3.3 Contrat JSON proposé vers le frontend

Le frontend ne doit jamais recevoir de chemin S3 brut ni de secret. Il reçoit des identifiants ou des URLs résolues côté serveur.

```ts
type Side = "D" | "G" | "";

interface DemoPhoto {
  individu: string;
  cote: Side;
  fichier_origine: string;
  /** Identifiant opaque résolu par l'API, jamais une URL signée exposée dans le code. */
  imageId: string;
  sha256?: string;
}

interface DemoCandidate {
  individu: string;
  score: number;
  D?: number;
  G?: number;
}

interface DemoProposition {
  photos: DemoPhoto[];
  candidats: DemoCandidate[];
  reponse: string[];
}

interface DemoPayload {
  bestOf: string;
  catalogue: string;
  individus: string[];
  propositions: Record<string, DemoProposition>;
  cataloguePhotos: Record<string, Partial<Record<"D" | "G", string>>>;
  pagination: { pageSize: 12; totalPages: number };
}
```

Variante possible : remplacer `imageId` par une URL signée à courte durée. Dans ce cas, la durée de vie et le domaine doivent être documentés, et aucune clé ne doit apparaître dans le bundle client.

## 4. Décision d’architecture à trancher

Trois chemins sont possibles. Le premier est recommandé pour la première version ; le second est un POC à instruire avant de l’adopter.

### Option A — rendu côté serveur, matching en amont (recommandé pour la parité)

- Next.js lit `derived/propositions/<best_of>.csv` ou un JSON généré par le pipeline Python.
- Les photos sont servies par une route API qui résout `imageId` vers le bucket.
- Le frontend ne calcule rien : il affiche les propositions et la galerie.
- Avantage : parité exacte avec Python, aucun secret côté client, faible risque.
- À vérifier : le CSV précalculé doit donner les mêmes top 10 que `propose()` sur le jeu de référence. La démo Gradio recalcule aujourd’hui depuis les empreintes ; ne pas supposer que les deux sont identiques sans test.

### Option B — POC Next.js + ONNX dans le navigateur

- Exporter CetaceaNet vers ONNX depuis le code Python, avec le même prétraitement (768 × 768, normalization ImageNet, moyenne photo + miroir, norme 1).
- Charger l’index `cetaceanet.npy` côté navigateur et faire le produit scalaire en JavaScript/WASM.
- État actuel : aucun `.onnx` n’existe dans le dépôt, aucune dépendance `onnxruntime` côté frontend, et aucun artefact binaire n’est versionné. L’export doit être produit côté Python, avec des poids figés (`last.ckpt`, pas `model.safetensors`), puis stocké hors Git.
- Critères de go/no-go à mesurer avant de choisir cette option :
  - taille du modèle et de l’index téléchargés ;
  - temps de chargement et mémoire utilisée ;
  - latence p50/p95 d’inférence sur un navigateur de référence, avec un seuil à fixer avant le POC ;
  - identité des top 10 avec Python sur le jeu de test ;
  - absence de secrets et de photos non autorisées dans le bundle.
- Le prétraitement et l’export ONNX restent de la responsabilité du code Python/ML. Le frontend consomme un artefact documenté, il ne réimplémente pas le modèle.

### Option C — hybride

- Upload ou sélection de photo côté navigateur, calcul de l’empreinte côté serveur, recherche k-NN côté navigateur contre un index statique.
- Utile seulement si l’inférence navigateur est impossible mais que la latence de recherche doit rester locale.

**Décision attendue avant implémentation :** retenir A pour la parité, puis lancer le POC B comme tâche séparée. Ne pas mélanger le port UI et le POC ONNX dans la même PR.

## 5. Accès aux données, sécurité et déploiement

- Le bucket est privé ; son nom n’est pas versionné. Les variables `S3_ENDPOINT_URL`, `S3_REGION`, `S3_BUCKET`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` restent côté serveur.
- Aucune variable `NEXT_PUBLIC_*` ne doit contenir ces valeurs. Les variables publiques sont figées au build et visibles dans le navigateur.
- L’authentification facultative `DEMO_PASSWORD` / `DEMO_USER` doit être vérifiée côté serveur.
- Les photos ne sont pas versionnées. Utiliser un répertoire temporaire ou un streaming ; ne pas copier `curated/` dans `frontend/public`.
- Les noms de fichiers `curated/` peuvent contenir le nom du photographe : ne jamais exposer le chemin brut au navigateur, même dans une URL signée.
- La route d’images doit refuser tout identifiant hors de l’ensemble fourni par le payload, pour éviter un accès arbitraire au bucket.
- L’application reste déployée sur `cetolog-web` via [`frontend_ci/README.md`](../frontend_ci/README.md). Les variables S3 et d’auth sont à renseigner dans la console Clever Cloud, pas dans le dépôt.
- Le contenu de `frontend/` reste limité au front : pas de module `dorsalmatch`, pas de `.env`, pas de logique Python.

## 6. Découpage en tâches

| Phase | Contenu | Critère de terminé |
|---|---|---|
| 0 | Ce document et les décisions ouvertes validées. | Spec relue, arbitrage A/B/C écrit. |
| 1 | Structure UI, types TypeScript, états loading/error/empty, fixtures synthétiques. Aucune photo Miraceti versionnée. Aucun runner de test n’existe encore dans `frontend/` : prévoir une reproduction manuelle documentée. Les hooks racine refusent `.csv`, `.npy` et les fichiers > 5 Mo : les fixtures doivent rester légères (JSON/TS). | `lint`, `format:check`, `build` OK ; parcours reproductible avec des données fictives. |
| 2 | Adaptateur de données serveur + route d’images + auth + branchement sur le bucket. | Les mêmes individus, top 10 et scores que la démo sur un jeu de référence. |
| 3 | POC ONNX séparé, sans remplacer la Phase 2. | Métriques de latence/taille enregistrées et décision go/no-go écrite. |
| 4 | Panneau d’explicabilité, seulement si besoin confirmé. | Traitement asynchrone ou mise en cache documentée, sans bloquer l’UI. |

Chaque phase donne lieu à une branche courte et une PR ciblée, selon [`frontend/AGENTS.md`](../../frontend/AGENTS.md).

## 7. Critères d’acceptation de la parité

Pour un best-of et un catalogue donnés :

- la liste des individus est identique à celle de la démo, y compris l’ordre `IND2` avant `IND10` ;
- sélectionner un individu affiche les mêmes photos et les mêmes 10 candidats ;
- les scores affichés arrondis à 2 décimales correspondent à ceux de Python ;
- les candidats `>= 0.97` n’apparaissent pas et sont consignés dans `reponse` dans le contrat, sans obligation d’affichage ;
- la pagination affiche 12 individus par page et borne correctement les pages ;
- les photos manquantes utilisent le même placeholder gris ;
- les états de chargement, d’erreur et vide sont présents et accessibles au clavier ;
- le bundle client ne contient ni clé S3, ni chemin de bucket, ni photo privée ;
- `npm run lint`, `npm run format:check` et `npm run build` passent depuis `frontend/`.

## 8. Questions ouvertes

1. Consommer `derived/propositions/<best_of>.csv` tel quel, ou recalculer depuis les empreintes côté serveur ? Recommandation : consommer le CSV après avoir validé l’égalité avec `propose()`.
2. Faut-il conserver l’authentification basique dans la première version ? Recommandation : oui, puisqu’elle existe dans la démo.
3. Comment servir les images privées : proxy via route API ou URLs signées courtes ? Recommandation : proxy, plus simple à sécuriser.
4. Le POC ONNX doit-il être fait avant la Phase 2 ou après ? Recommandation : après, pour ne pas bloquer le port UI.
5. Le panneau d’explicabilité est-il attendu dans la première démonstration ? Recommandation : non, car il est coûteux et nécessite PyTorch.
6. Quelle cible chiffrée de latence, de taille et de mémoire pour le POC ONNX ? Le dépôt n’en définit aucune.
7. Faut-il figer explicitement `BEST_OF` et `CATALOGUE` dans le contrat du POC, pour éviter que `latest()` change de livraison entre deux démonstrations ?

## 9. Arbitrages retenus pour la phase 2

- Source : `derived/propositions/<best_of>.csv`, après vérification de parité avec `propose()`. Sur la livraison `2026-11-06_bestof_20230307_sete`, les 24 individus et les 240 lignes du CSV correspondent aux scores recalculés depuis les `.npy` (0 écart).
- Livraisons : lues dans les colonnes `best_of` et `catalogue` du CSV, plutôt que choisies par `latest()`. Le fichier de propositions peut être figé par `DEMO_PROPOSITIONS_KEY`.
- Accès aux données : SDK S3 dans Next.js, credentials serveur dans Clever Cloud, sans variable `NEXT_PUBLIC_*`.
- Images : proxy via route API allowlistée, pas d’URLs signées. Aucun chemin `curated/` ni `fichier_origine` exposé au navigateur.
- Auth : Basic Auth facultative, calquée sur `DEMO_USER` / `DEMO_PASSWORD` de Gradio.
- Périmètre : explicabilité et POC ONNX restent hors phase 2.

## 10. Références

- [`demo/app.py`](../../demo/app.py) — comportement de référence.
- [`demo/propositions.py`](../../demo/propositions.py) — règles de matching.
- [`demo/explanations.py`](../../demo/explanations.py) — explicabilité, hors première version.
- [`dorsalmatch/match.py`](../../dorsalmatch/match.py) — recherche cosinus.
- [`docs/cetolog_demo/README.md`](README.md) — contexte de la démo.
- [`docs/miraceti_data/catalogue.md`](../miraceti_data/catalogue.md) — contrats des fichiers `curated/` et `derived/`.
- [`docs/cetolog_ml/fonctionnement.md`](../cetolog_ml/fonctionnement.md) — chaîne modèle → empreintes → recherche.
- [`docs/cetolog_ml/utiliser.md`](../cetolog_ml/utiliser.md) — coûts des techniques d’explicabilité.
- [`README.md`](../../README.md) — contexte produit et lien Figma « le matching, étape par étape » (ligne 15).
- [`frontend/AGENTS.md`](../../frontend/AGENTS.md) — règles de contribution frontend.
