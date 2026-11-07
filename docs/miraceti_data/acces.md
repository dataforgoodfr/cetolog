# Accéder aux données

Toutes les données sont dans le bucket S3 **privé** `cetolog-data`, hébergé sur Clever Cloud (Cellar, compatible S3). On y accède avec **`pipeline.storage`**, le module du dépôt : il n'y a rien d'autre à installer.

## 1. Les accès

Les accès (une clé et un secret) sont **à demander à `mandresyandri`**. Ils vont dans un fichier `.env`, à la racine du dépôt :

```bash
cp .env.example .env
```

```text
S3_ENDPOINT_URL=https://cellar-c2.services.clever-cloud.com
S3_REGION=us-east-1
S3_BUCKET=cetolog-data
AWS_ACCESS_KEY_ID=<la clé reçue>
AWS_SECRET_ACCESS_KEY=<le secret reçu>
```

`.env` n'est jamais versionné : le contrôle de commit le refuse.

## 2. Vérifier la connexion

```bash
uv run python -m pipeline.storage check
```

Si tout va bien, la commande affiche `connexion OK : cetolog-data`. Sinon, l'erreur dit ce qui manque : une variable de `.env`, ou un accès refusé.

## 3. Ce dont tu as besoin selon ton métier

Le bucket est rangé comme ta copie locale `data/` : les trois couches, puis un dossier par jeu (`catalogue`, `best_of`, `historique`).

```text
raw/<jeu>/<livraison>.zip                      les zips de Miraceti, tels que livrés
curated/<jeu>/photos/<livraison>/<individu>/   les photos prêtes
curated/<jeu>/manifests/<livraison>.csv        une ligne par photo
derived/embeddings/<jeu>/<livraison>/          les empreintes
derived/propositions/<best_of>.csv             les candidats de chaque individu d'un best-of
```

### Tu travailles sur la pipeline

Tu pars des zips livrés par Miraceti, la couche iso-source.

```bash
uv run python -m pipeline.storage pull
```

`pull` copie `raw/` du bucket dans `data/raw/`, en sautant ce qui est déjà là. Comptez quelques minutes : le catalogue pèse 2,6 Go. Ensuite, [le catalogue](catalogue.md#comment-chaque-couche-est-produite) explique comment produire `curated/` et `derived/`.

### Tu travailles sur le ML

Tu as besoin des photos prêtes (`curated/`) et des empreintes (`derived/`), pas des zips : récupère-les telles quelles. Depuis la racine du dépôt :

```python
from pipeline.storage import connect

bucket = connect()  # lit .env
bucket.pull(prefix="curated/")  # les photos prêtes et leurs manifestes : environ 3 Go
bucket.pull(prefix="derived/")  # les empreintes et les propositions : quelques Mo
```

L'historique ne se reconstruit pas avec la pipeline : on le récupère prêt dans le bucket.

C'est fait une fois : ensuite, tu travailles sur `data/` en local, avec `dorsalmatch` et [le notebook](../../notebooks/metriques_catalogue.ipynb).

### Tu veux juste un fichier

`pipeline.storage` s'utilise aussi en Python, pour lister ou télécharger un fichier précis sans tout récupérer :

```python
from pipeline.storage import connect

bucket = connect()  # lit .env
bucket.list_keys("curated/historique/")  # les fichiers sous ce préfixe
bucket.download("curated/historique/manifests/2026-10-29_miraceti.csv", "historique.csv")
```

## 4. Envoyer des données dans le bucket

> **NE JAMAIS supprimer `raw/` dans le bucket.** Ce sont les zips tels que livrés par Miraceti : la seule couche irremplaçable. Si on la perd, il faut tout redemander à Miraceti. `curated/` et `derived/` se reconstruisent avec la pipeline, `raw/` non.

C'est possible avec `pipeline.storage`, mais **attention** : tout ce qui arrive dans le bucket doit être décrit dans [le catalogue des données](catalogue.md). Avant d'envoyer quoi que ce soit, **mets à jour le catalogue** (le jeu, la livraison, ses chiffres, ses pièges), et préviens l'équipe.
