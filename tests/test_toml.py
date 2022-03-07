import pytest
import tomli

from .common import load_vd_sheet

SAMPLE_FILE = "tests/sample.toml"


@pytest.fixture(scope="session")
def sample_data():
    return tomli.load(open(SAMPLE_FILE, "rb"))


@pytest.fixture(scope="session")
def sample_sheet():
    return load_vd_sheet(SAMPLE_FILE)


def test_toml_columns(sample_data, sample_sheet):
    """We should have a column for each key in the loaded dict"""
    assert set(sample_data) == set(c.name for c in sample_sheet.columns)


def test_toml_rows(sample_sheet):
    """For a valid, non-empty TOML file we expect 1 loaded row"""
    assert len(sample_sheet.rows) == 1
