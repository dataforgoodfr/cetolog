from __future__ import annotations

import mimetypes
import os
import sys
from pathlib import Path

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

# TODO: repenser la structure du S3 : données prêtes pour le ML, réindexation, identifiées et à identifier

# CONSTANTES
REQUIRED_VARIABLES = (
    "S3_ENDPOINT_URL", "S3_REGION", 
    "S3_BUCKET", "AWS_ACCESS_KEY_ID", 
    "AWS_SECRET_ACCESS_KEY"
)
DATA = Path("data")  # réplique locale du bucket : mêmes dossiers, mêmes chemins


# Récupération des variables d'environnements -> .env TODO: penser à demander les credentials
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
    
    # Par défaut, boto3 envoie sans Content-Length, avec une somme de contrôle en fin de flux : Cellar refuse.
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
        """Vérifie que les accès ouvrent bien le bucket : une erreur S3 est levée sinon."""
        self.client.head_bucket(Bucket=self.name)

    def list_keys(self, prefix: str) -> list[str]:
        """Les fichiers sous ce préfixe, sans les objets vides qui font exister les dossiers."""
        pages = self.client.get_paginator("list_objects_v2").paginate(Bucket=self.name, Prefix=prefix)
        return [item["Key"] for page in pages for item in page.get("Contents", []) if not item["Key"].endswith("/")]

    def head(self, key: str) -> dict | None:
        """Les informations d'un fichier, ou None s'il n'existe pas. Toute autre erreur S3 est levée."""
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

    def pull(self, data: Path = DATA) -> None:
        """Copie raw/ du bucket vers data/raw/, en sautant ce qui est déjà là."""
        received = 0
        for key in self.list_keys("raw/"):
            path = data / key
            if path.exists():
                continue

            # Fichier temporaire : un téléchargement coupé ne passe pas pour un fichier complet
            path.parent.mkdir(parents=True, exist_ok=True)
            partial = path.with_name(path.name + ".part")
            print(f"téléchargement : {key}", flush=True)
            self.download(key, partial)
            partial.rename(path)
            received += 1

        print(f"{received} fichiers récupérés dans {data / 'raw'}")

    def push(self, data: Path = DATA) -> None:
        """Envoie data/curated/ vers le bucket : les photos d'abord, les manifestes en dernier. raw/ n'est jamais touché."""
        sent = 0
        for folder in ("photos", "manifests"):
            for path in sorted((data / "curated" / folder).rglob("*")):
                key = path.relative_to(data).as_posix()
                if path.is_file() and not path.name.startswith(".") and self.head(key) is None:
                    self.upload(path, key)
                    sent += 1

        print(f"{sent} fichiers envoyés vers {self.name}")


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
