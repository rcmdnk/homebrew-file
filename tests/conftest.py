import os
from pathlib import Path

import pytest
from filelock import FileLock

from . import brew_file


@pytest.fixture(scope="session", autouse=True)
def check_brew(tmp_path_factory):
    root_tmp_dir = tmp_path_factory.getbasetemp().parent
    with FileLock(root_tmp_dir / "brew.lock"):
        bf = brew_file.BrewFile({})
        if not (Path(bf.opt["cache"]) / "api/formula.jws.json").exists():
            # pseudo code to download api json
            bf.helper.proc("brew search python")
    os.environ["HOMEBREW_API_AUTO_UPDATE_SECS"] = "100000"
    os.environ["HOMEBREW_AUTO_UPDATE_SECS"] = "100000"
    if "HOMEBREW_BREWFILE_VERBOSE" in os.environ:
        del os.environ["HOMEBREW_BREWFILE_VERBOSE"]


@pytest.fixture(scope="session", autouse=False)
def tap(tmp_path_factory):
    root_tmp_dir = tmp_path_factory.getbasetemp().parent
    with FileLock(root_tmp_dir / "tap.lock"):
        bf = brew_file.BrewFile({})
        bf.helper.proc("brew tap rcmdnk/rcmdnkpac")
        bf.helper.proc("brew tap rcmdnk/rcmdnkcask")


@pytest.fixture(scope="session", autouse=False)
def python(tmp_path_factory):
    root_tmp_dir = tmp_path_factory.getbasetemp().parent
    with FileLock(root_tmp_dir / "python.lock"):
        bf = brew_file.BrewFile({})
        bf.helper.proc("brew install python@3.10")
