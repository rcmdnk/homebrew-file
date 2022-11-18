import pytest

from . import brew_file


@pytest.fixture(scope="session", autouse=True)
def check_brew():
    brew_file.BrewFile({})
