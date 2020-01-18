import gzip
import json
import os
import shutil
import subprocess

import boto3
import pytest

import plugins

JSON_SAMPLE = 'tests/sample.json'
BUCKET = 'visidata-test'
KEY = 'nested/folders/sample.json'


@pytest.fixture(scope='session', autouse=True)
def moto_s3():
    '''
    Because we're treating VisiData as a black box, use a shared mock
    S3 endpoint for the duration of the test session. We can direct
    both boto3 and the vds3 plugin to use the same local endpoint.
    '''
    with subprocess.Popen(['moto_server', 's3', '-p3000']) as proc:
        yield
        proc.kill()

@pytest.fixture(scope='session')
def s3_resource():
    return boto3.resource(
        's3', region_name='us-east-1', endpoint_url='http://localhost:3000'
    )

def test_local_roundtrip(tmp_path):
    '''
    Be sure that a round trip of our sample JSON file works
    as expected before getting S3 into the mix.
    '''
    out = tmp_path / 'sample.json'
    p = subprocess.run(['vd', '-b', JSON_SAMPLE, '-o', out])
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
    subprocess.run(['vd', '-b', f's3://{BUCKET}/{KEY}', '-o', out])
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
    subprocess.run(['vd', '-b', f's3://{BUCKET}/{KEY}.gz', '-o', out])
    with open(JSON_SAMPLE, 'r') as f1, open(out, 'r') as f2:
        assert json.load(f1) == json.load(f2)
