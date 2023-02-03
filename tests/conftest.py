import logging
import sys

import pytest

from . import brew_file


@pytest.fixture(scope="session", autouse=True)
def check_brew():
    brew_file.BrewFile({})


@pytest.fixture
def ch() -> logging.StreamHandler:
    ch = logging.StreamHandler(stream=sys.stdout)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(brew_file.LogFormatter())
    return ch
