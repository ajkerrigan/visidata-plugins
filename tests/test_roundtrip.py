import gzip
import json
import shutil
import multiprocessing
from collections import namedtuple

import boto3
import botocore
import moto.server
import pytest
from visidata import vd, AttrDict, Path

JSON_SAMPLE = 'tests/sample.json'
BUCKET = 'visidata-test'
KEY = 'nested/folders/sample.json'


@pytest.fixture(scope='session', autouse=True)
def path_info():
    filename = 'sample.json'
    return AttrDict({
        'base_filename': filename,
        'local_filepath': f'tests/{filename}',
        's3_bucket': 'visidata-test',
        's3_key': f'nested/folders/{filename}',
    })

@pytest.fixture(scope='session')
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
def s3_setup(moto_s3, tmp_path_factory):
    resource = boto3.resource(
        's3',
        region_name='us-east-1',
        config=botocore.config.Config(retries=dict(max_attempts=10)),
        endpoint_url='http://localhost:3000',
    )
    resource.create_bucket(Bucket=BUCKET)
    obj = resource.Object(BUCKET, KEY)
    obj.upload_file(JSON_SAMPLE)
    obj.wait_until_exists()

    gzpath = tmp_path_factory.mktemp('gzip') / 'sample.json.gz'
    obj = resource.Object(BUCKET, f'{KEY}.gz')
    with open(JSON_SAMPLE, 'rb') as uncompressed, gzip.open(gzpath, 'wb') as compressed:
        shutil.copyfileobj(uncompressed, compressed)
    obj.upload_file(str(gzpath))
    obj.wait_until_exists()

def load_vd_sheet(inpath: str):
    '''
    Load a file with VisiData, and return the
    sheet object.
    '''
    vd.loadConfigAndPlugins(AttrDict({}))
    sheet = vd.openSource(inpath)
    sheet.reload()
    vd.sync()
    return sheet


def test_local_roundtrip(tmp_path):
    '''
    Be sure that a round trip of our sample JSON file works
    as expected before getting S3 into the mix.
    '''
    out = tmp_path / 'sample.json'
    sheet = load_vd_sheet(JSON_SAMPLE)
    vd.save_json(Path(out), sheet)
    with open(JSON_SAMPLE, 'r') as f1, open(out, 'r') as f2:
        assert json.load(f1) == json.load(f2)


def test_s3_roundtrip(tmp_path, s3_setup):
    '''
    Upload a sample file to our mock S3 server, then confirm that
    a VisiData round trip brings back the same data.
    '''
    out = tmp_path / 'sample.json'
    sheet = load_vd_sheet(f's3://{BUCKET}/{KEY}')
    vd.save_json(Path(out), sheet)
    with open(JSON_SAMPLE, 'r') as f1, open(out, 'r') as f2:
        assert json.load(f1) == json.load(f2)


def test_s3_gzip_roundtrip(tmp_path, s3_setup):
    '''
    Zip and then upload a sample file to our mock S3 server. Confirm
    that a VisiData round trip handles the decompression and outputs
    the same data.
    '''
    out = tmp_path / 'sample.json'
    sheet = load_vd_sheet(f's3://{BUCKET}/{KEY}.gz')
    vd.save_json(Path(out), sheet)
    with open(JSON_SAMPLE, 'r') as f1, open(out, 'r') as f2:
        assert json.load(f1) == json.load(f2)

# def test_s3_download(tmp_path, s3_resource):
#     '''Make sure that we can download files and nothing gets
#     lost in translation.
#     '''
