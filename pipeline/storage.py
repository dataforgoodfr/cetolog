from __future__ import annotations

import mimetypes
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

# CONSTANTES
REQUIRED_VARIABLES = (
    "S3_ENDPOINT_URL", "S3_REGION", 
    "S3_BUCKET", "AWS_ACCESS_KEY_ID", 
    "AWS_SECRET_ACCESS_KEY"
)
DATA = Path("data")
PUSHED = (
    "curated/catalogue/photos", "curated/catalogue/manifests",
    "curated/best_of/photos", "curated/best_of/manifests",
    "curated/historique/photos", "curated/historique/manifests",
    "derived/embeddings", "derived/propositions",
)


# Les accès au bucket, lus dans .env
def load_env(path: str | Path = ".env") -> None:
    path = Path(path)
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


# Connexion au S3
def connect() -> Bucket:
    load_env()
    missing = [variable for variable in REQUIRED_VARIABLES if not os.environ.get(variable)]
    if missing:
        raise RuntimeError(f"Variables manquantes : {', '.join(missing)}")
    
    # Cellar refuse les sommes de contrôle par défaut de boto3
    config = Config(
        request_checksum_calculation="when_required", 
        response_checksum_validation="when_required"
    )
    client = boto3.client(
        "s3", endpoint_url=os.environ["S3_ENDPOINT_URL"], 
        region_name=os.environ["S3_REGION"],
        config=config
    )

    return Bucket(client, os.environ["S3_BUCKET"])


# Attributs et méthodes du Bucket
class Bucket:
    def __init__(self, client, name: str):
        self.client = client
        self.name = name

    def check(self) -> None:
        self.client.head_bucket(Bucket=self.name)

    def list_keys(self, prefix: str) -> list[str]:
        pages = self.client.get_paginator("list_objects_v2").paginate(Bucket=self.name, Prefix=prefix)
        return [item["Key"] for page in pages for item in page.get("Contents", []) if not item["Key"].endswith("/")]

    def head(self, key: str) -> dict | None:
        try:
            return self.client.head_object(Bucket=self.name, Key=key)
        except ClientError as error:
            if error.response["Error"]["Code"] in ("404", "NoSuchKey"):
                return None
            raise

    def download(self, key: str, path: str | Path) -> None:
        body = self.client.get_object(Bucket=self.name, Key=key)["Body"]
        with open(path, "wb") as file:
            for block in body.iter_chunks(1024 * 1024):
                file.write(block)

    def upload(self, path: str | Path, key: str, metadata: dict[str, str] | None = None) -> None:
        with open(path, "rb") as file:
            self.client.put_object(
                Bucket=self.name, Key=key, Body=file,
                ContentType=mimetypes.guess_type(key)[0] or "application/octet-stream",
                Metadata=metadata or {},
            )

    def fetch(self, path: str | Path, data: Path = DATA) -> Path:
        """Télécharge le fichier s'il manque."""
        path = Path(path)
        if not path.exists():
            # .part : un téléchargement coupé ne passe pas pour complet
            path.parent.mkdir(parents=True, exist_ok=True)
            partial = path.with_name(path.name + ".part")
            self.download(path.relative_to(data).as_posix(), partial)
            partial.rename(path)
        return path

    def pull(self, data: Path = DATA, prefix: str = "raw/") -> None:
        received = 0
        for key in self.list_keys(prefix):
            if not (data / key).exists():
                print(f"téléchargement : {key}", flush=True)
                self.fetch(data / key, data)
                received += 1

        print(f"{received} fichiers récupérés dans {data / prefix}")

    def push(self, data: Path = DATA, workers: int = 16) -> None:
        """Envoie PUSHED sans écraser, en parallèle. raw/ n'est jamais touché."""
        # Une liste du bucket par dossier, plutôt qu'une requête par fichier
        todo = []
        for folder in PUSHED:
            existing = set(self.list_keys(f"{folder}/"))
            for path in sorted((data / folder).rglob("*")):
                key = path.relative_to(data).as_posix()
                if path.is_file() and not path.name.startswith(".") and key not in existing:
                    todo.append((path, key))

        # Le client boto3 se partage entre threads
        with ThreadPoolExecutor(workers) as pool:
            for sent, _ in enumerate(pool.map(lambda item: self.upload(*item), todo), start=1):
                if sent % 200 == 0:
                    print(f"{sent} / {len(todo)}", flush=True)

        print(f"{len(todo)} fichiers envoyés vers {self.name}")


# python -m pipeline.storage check, pull ou push
if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "check"
    bucket = connect()
    bucket.check()

    if command == "check":
        print(f"connexion OK : {bucket.name}")
    elif command == "pull":
        bucket.pull()
    elif command == "push":
        bucket.push()
    else:
        sys.exit(f"Commande inconnue : {command}. Commandes : check, pull, push")
