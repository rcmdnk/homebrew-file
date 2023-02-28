import logging
import sys

import pytest
from filelock import FileLock

from . import brew_file


@pytest.fixture(scope="session", autouse=True)
def check_brew():
    brew_file.BrewFile({})


@pytest.fixture(scope="session", autouse=False)
def caplog_session_lock(tmp_path_factory, worker_id):
    if worker_id == "master":
        return

    root_tmp_dir = tmp_path_factory.getbasetemp().parent
    with FileLock(root_tmp_dir / "caplog.lock"):
        pass


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


@pytest.fixture(scope="function", autouse=False)
def caplog_locked(caplog_session_lock, caplog):
    caplog.set_level(logging.DEBUG)
    return caplog
