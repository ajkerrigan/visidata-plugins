import gzip
import json
import shutil
import multiprocessing

import boto3
import botocore
import moto.server
import pytest
from visidata import vd, AttrDict, Path

JSON_SAMPLE = 'tests/sample.json'
BUCKET = 'visidata-test'
KEY = 'nested/folders/sample.json'
BOTO_CONFIG = botocore.config.Config(retries=dict(max_attempts=10))


@pytest.fixture(scope='session', autouse=True)
def moto_s3():
    '''
    Because we're treating VisiData as a black box, use a shared mock
    S3 endpoint for the duration of the test session. We can direct
    both boto3 and the vds3 plugin to use the same local endpoint.
    '''
    multiprocessing.set_start_method('spawn')
    proc = multiprocessing.Process(
        target=moto.server.main, kwargs={'argv': ('s3', '-p', '3000')}
    )
    proc.start()
    yield
    proc.terminate()


@pytest.fixture(scope='session')
def s3_resource():
    return boto3.resource(
        's3',
        region_name='us-east-1',
        config=BOTO_CONFIG,
        endpoint_url='http://localhost:3000',
    )


def visidata_roundtrip(inpath, outpath):
    '''
    Load and save a file with VisiData.

    inpath: str
    outpath: visidata.Path
    '''
    vd.loadConfigAndPlugins(AttrDict({}))
    sheet = vd.openSource(inpath)
    sheet.reload()
    vd.sync()
    vd.save_json(outpath, sheet)


def test_local_roundtrip(tmp_path):
    '''
    Be sure that a round trip of our sample JSON file works
    as expected before getting S3 into the mix.
    '''
    out = tmp_path / 'sample.json'
    visidata_roundtrip(JSON_SAMPLE, Path(out))
    with open(JSON_SAMPLE, 'r') as f1, open(out, 'r') as f2:
        assert json.load(f1) == json.load(f2)


def test_s3_roundtrip(tmp_path, s3_resource):
    '''
    Upload a sample file to our mock S3 server, then confirm that
    a VisiData round trip brings back the same data.
    '''
    out = tmp_path / 'sample.json'
    s3_resource.create_bucket(Bucket=BUCKET)
    obj = s3_resource.Object(BUCKET, KEY)
    obj.upload_file(JSON_SAMPLE)
    obj.wait_until_exists()
    visidata_roundtrip(f's3://{BUCKET}/{KEY}', Path(out))
    with open(JSON_SAMPLE, 'r') as f1, open(out, 'r') as f2:
        assert json.load(f1) == json.load(f2)


def test_s3_gzip_roundtrip(tmp_path, s3_resource):
    '''
    Zip and then upload a sample file to our mock S3 server. Confirm
    that a VisiData round trip handles the decompression and outputs
    the same data.
    '''
    gzpath = tmp_path / 'sample.json.gz'
    out = tmp_path / 'sample.json'
    s3_resource.create_bucket(Bucket=BUCKET)
    obj = s3_resource.Object(BUCKET, f'{KEY}.gz')
    with open(JSON_SAMPLE, 'rb') as uncompressed, gzip.open(gzpath, 'wb') as compressed:
        shutil.copyfileobj(uncompressed, compressed)
    obj.upload_file(str(gzpath))
    obj.wait_until_exists()
    visidata_roundtrip(f's3://{BUCKET}/{KEY}.gz', Path(out))
    with open(JSON_SAMPLE, 'r') as f1, open(out, 'r') as f2:
        assert json.load(f1) == json.load(f2)
