import gzip
import json
import multiprocessing
import shutil

import boto3
import botocore
import moto.server
import pytest
from visidata import AttrDict, Path, vd

from .common import load_vd_sheet


@pytest.fixture(scope="session", autouse=True)
def path_info():
    filename = "sample.json"
    yield AttrDict(
        {
            "base_filename": filename,
            "gzip_filename": f"{filename}.gz",
            "local_file": f"tests/{filename}",
            "s3_bucket": "visidata-test",
            "s3_key": f"nested/folders/{filename}",
        }
    )


@pytest.fixture(scope="session")
def moto_s3():
    """
    Because we're treating VisiData as a black box, use a shared mock
    S3 endpoint for the duration of the test session. We can direct
    both boto3 and the vds3 plugin to use the same local endpoint.
    """
    multiprocessing.set_start_method("spawn")
    proc = multiprocessing.Process(
        target=moto.server.main, kwargs={"argv": ("s3", "-p", "3000")}
    )
    proc.start()
    yield
    proc.terminate()


@pytest.fixture(scope="session")
def s3_setup(moto_s3, tmp_path_factory, path_info):
    resource = boto3.resource(
        "s3",
        region_name="us-east-1",
        config=botocore.config.Config(retries=dict(max_attempts=10)),
        endpoint_url="http://localhost:3000",
    )
    bucket, key = path_info.s3_bucket, path_info.s3_key

    resource.create_bucket(Bucket=bucket)
    obj = resource.Object(bucket, key)
    obj.upload_file(path_info.local_file)
    obj.wait_until_exists()

    gzpath = tmp_path_factory.mktemp("gzip") / path_info.gzip_filename
    obj = resource.Object(bucket, f"{key}.gz")
    with open(path_info.local_file, "rb") as uncompressed, gzip.open(
        gzpath, "wb"
    ) as compressed:
        shutil.copyfileobj(uncompressed, compressed)
    obj.upload_file(str(gzpath))
    obj.wait_until_exists()


def test_local_roundtrip(tmp_path, path_info):
    """
    Be sure that a round trip of our sample JSON file works
    as expected before getting S3 into the mix.
    """
    out = tmp_path / "sample.json"
    sheet = load_vd_sheet(path_info.local_file)
    vd.save_json(Path(out), sheet)
    with open(path_info.local_file, "r") as f1, open(out, "r") as f2:
        assert json.load(f1) == json.load(f2)


def test_s3_roundtrip(tmp_path, s3_setup, path_info):
    """
    Upload a sample file to our mock S3 server, then confirm that
    a VisiData round trip brings back the same data.
    """
    out = tmp_path / "sample.json"
    sheet = load_vd_sheet(f"s3://{path_info.s3_bucket}/{path_info.s3_key}")
    vd.save_json(Path(out), sheet)
    with open(path_info.local_file, "r") as f1, open(out, "r") as f2:
        assert json.load(f1) == json.load(f2)


def test_s3_gzip_roundtrip(tmp_path, s3_setup, path_info):
    """
    Zip and then upload a sample file to our mock S3 server. Confirm
    that a VisiData round trip handles the decompression and outputs
    the same data.
    """
    out = tmp_path / "sample.json"
    sheet = load_vd_sheet(f"s3://{path_info.s3_bucket}/{path_info.s3_key}.gz")
    vd.save_json(Path(out), sheet)
    with open(path_info.local_file, "r") as f1, open(out, "r") as f2:
        assert json.load(f1) == json.load(f2)


def test_s3_download(tmp_path, s3_setup, path_info):
    """Make sure that we can download files and nothing gets
    lost along the way.
    """
    sheet = load_vd_sheet(f"s3://{path_info.s3_bucket}")
    sheet.download(sheet.rows, Path(tmp_path))
    vd.sync()
    assert {path_info.base_filename, path_info.gzip_filename} <= set(
        f.name for f in Path(tmp_path).glob("**/*")
    )
