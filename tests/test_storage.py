import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws

from pipeline.storage import REQUIRED_VARIABLES, Bucket, connect


# Faux bucket S3, en mémoire
@pytest.fixture
def bucket():
    with mock_aws():
        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket="test")
        yield Bucket(client, "test")


# Petit fichier local à envoyer
@pytest.fixture
def source(tmp_path):
    path = tmp_path / "source.txt"
    path.write_text("cetolog")
    return path


# Connexion au S3
def test_connect_refuses_missing_or_empty_variables(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for variable in REQUIRED_VARIABLES:
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "")

    with pytest.raises(RuntimeError, match="AWS_ACCESS_KEY_ID"):
        connect()


def test_check_refuses_an_unknown_bucket(bucket):
    with pytest.raises(ClientError):
        Bucket(bucket.client, "inconnu").check()


# Méthodes du Bucket
def test_upload_then_download(bucket, source, tmp_path):
    bucket.upload(
        source, 
        "tests/essai.txt", 
        {"sha256": "abc"}
    )
    bucket.download("tests/essai.txt", tmp_path / "copie.txt")

    assert (tmp_path / "copie.txt").read_text() == "cetolog"
    assert bucket.head("tests/essai.txt")["Metadata"] == {"sha256": "abc"}


def test_list_keys_ignores_folder_objects(bucket, source):
    bucket.client.put_object(Bucket="test", Key="raw/photos/")
    bucket.upload(source, "raw/photos/a.zip")

    assert bucket.list_keys("raw/photos/") == ["raw/photos/a.zip"]


def test_head_returns_none_for_a_missing_file(bucket):
    assert bucket.head("absent.txt") is None


def test_head_does_not_hide_other_errors():
    class RefusedClient:
        def head_object(self, Bucket, Key):
            raise ClientError({"Error": {"Code": "403"}}, "HeadObject")

    with pytest.raises(ClientError):
        Bucket(RefusedClient(), "test").head("photo.jpg")


# Pull : du bucket à data/raw/
def test_pull_copies_raw_only(bucket, tmp_path):
    bucket.client.put_object(Bucket="test", Key="raw/observations/")
    bucket.client.put_object(Bucket="test", Key="raw/photos/a_photos.zip", Body=b"zip")
    bucket.client.put_object(Bucket="test", Key="curated/manifests/a.csv", Body=b"csv")
    bucket.pull(tmp_path)

    assert (tmp_path / "raw" / "photos" / "a_photos.zip").read_bytes() == b"zip"
    assert not (tmp_path / "curated").exists()
    assert not list(tmp_path.rglob("*.part"))


def test_pull_does_not_download_twice(bucket, tmp_path, capsys):
    bucket.client.put_object(Bucket="test", Key="raw/photos/a_photos.zip", Body=b"zip")
    bucket.pull(tmp_path)
    capsys.readouterr()
    bucket.pull(tmp_path)

    assert "0 fichiers récupérés" in capsys.readouterr().out


# Push : de data/curated/ au bucket
@pytest.fixture
def data(tmp_path):
    for key in ("curated/photos/a/TUTR0025/photo.jpg", "curated/manifests/a.csv", "raw/photos/a_photos.zip", "curated/photos/.DS_Store"):
        path = tmp_path / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("contenu")
    return tmp_path


def test_push_sends_curated_only(bucket, data):
    bucket.push(data)

    assert set(bucket.list_keys("")) == {"curated/photos/a/TUTR0025/photo.jpg", "curated/manifests/a.csv"}


def test_push_sends_nothing_the_second_time(bucket, data, capsys):
    bucket.push(data)
    capsys.readouterr()
    bucket.push(data)

    assert "0 fichiers envoyés" in capsys.readouterr().out
