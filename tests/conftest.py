from __future__ import annotations

import os
from pathlib import Path

import pytest
from filelock import FileLock

from .brew_file import BrewFile


@pytest.fixture(scope='session', autouse=True)
def check_brew(tmp_path_factory: pytest.TempPathFactory) -> None:
    root_tmp_dir = tmp_path_factory.getbasetemp().parent
    with FileLock(root_tmp_dir / 'brew.lock'):
        bf = BrewFile({})
        if not (Path(bf.opt['cache']) / 'api/formula.jws.json').exists():
            # pseudo code to download api json
            bf.helper.proc('brew search python')
    for env in os.environ:
        if env.startswith('HOMEBREW_BREWFILE'):
            del os.environ[env]
    os.environ['HOMEBREW_API_AUTO_UPDATE_SECS'] = '100000'
    os.environ['HOMEBREW_AUTO_UPDATE_SECS'] = '100000'


@pytest.fixture(scope='session', autouse=False)
def tap(tmp_path_factory: pytest.TempPathFactory) -> list[str]:
    taps = ['rcmdnk/rcmdnkpac', 'rcmdnk/rcmdnkcask']
    root_tmp_dir = tmp_path_factory.getbasetemp().parent
    with FileLock(root_tmp_dir / 'tap.lock'):
        bf = BrewFile({})
        bf.helper.proc(f'brew tap {taps[0]}')
        bf.helper.proc(f'brew tap {taps[1]}')
    return taps


@pytest.fixture(scope='session', autouse=False)
def python(tmp_path_factory: pytest.TempPathFactory) -> str:
    python_formula = 'python@3.13'
    root_tmp_dir = tmp_path_factory.getbasetemp().parent
    with FileLock(root_tmp_dir / 'python.lock'):
        bf = BrewFile({})
        # To ignore 2to3 conflict with OS's python (@macOS on GitHub Actions)
        bf.helper.proc(f'brew install {python_formula}', exit_on_err=False)
    return python_formula
