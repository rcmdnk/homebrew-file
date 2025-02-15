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
    os.environ['HOMEBREW_API_AUTO_UPDATE_SECS'] = '100000'
    os.environ['HOMEBREW_AUTO_UPDATE_SECS'] = '100000'
    os.environ['HOMEBREW_BREWFILE_VERBOSE'] = 'info'
    os.environ['HOMEBREW_BREWFILE'] = ''
    os.environ['HOMEBREW_BREWFILE_BACKUP'] = ''
    os.environ['HOMEBREW_BREWFILE_LEAVES'] = ''
    os.environ['HOMEBREW_BREWFILE_ON_REQUEST'] = ''
    os.environ['HOMEBREW_BREWFILE_TOP_PACKAGES'] = ''
    os.environ['HOMEBREW_BREWFILE_FETCH_HEAD'] = ''
    os.environ['HOMEBREW_BREWFILE_EDITOR'] = 'vim'
    os.environ['HOMEBREW_BREWFILE_NO_INSTALL_FROM_API'] = ''
    os.environ['HOMEBREW_BREWFILE_APPSTORE'] = '-1'
    os.environ['HOMEBREW_BREWFILE_FULL_NAME'] = '0'
    os.environ['HOMEBREW_BREWFILE_WHALEBREW'] = '0'
    os.environ['HOMEBREW_BREWFILE_VSCODE'] = '0'
    os.environ['HOMEBREW_BREWFILE_CURSOR'] = '0'


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
