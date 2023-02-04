import logging
import sys

import pytest

from . import brew_file


@pytest.fixture(scope="session", autouse=True)
def check_brew():
    brew_file.BrewFile({})


@pytest.fixture(scope="session", autouse=False)
def tap():
    bf = brew_file.BrewFile({})
    bf.helper.proc("brew tap rcmdnk/rcmdnkpac")
    bf.helper.proc("brew tap rcmdnk/rcmdnkcask")


@pytest.fixture(scope="session", autouse=False)
def python():
    bf = brew_file.BrewFile({})
    bf.helper.proc("brew install python@3.10")


@pytest.fixture
def ch() -> logging.StreamHandler:
    ch = logging.StreamHandler(stream=sys.stdout)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(brew_file.LogFormatter())
    return ch
