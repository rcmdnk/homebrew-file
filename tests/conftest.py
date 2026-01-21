from __future__ import annotations

import getpass
import os
import warnings
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from .brew_file import BrewFile, BrewHelper, BrewInfo, is_mac

if TYPE_CHECKING:
    from _pytest.config import Config
    from _pytest.nodes import Item


def _parallel_test(config: Config) -> bool:
    return getattr(config, 'workerinput', None) is not None


@pytest.hookimpl(trylast=True)  # To run after marker filtering
def pytest_collection_modifyitems(config: Config, items: list[Item]) -> None:
    remaining = []
    destructive = []

    for item in items:
        if 'destructive' in item.keywords:
            destructive.append(item)
        else:
            remaining.append(item)

    if destructive:
        config.destructive_clean = True  # ty: ignore[unresolved-attribute]
        if _parallel_test(config):
            config.hook.pytest_deselected(items=destructive)
            items[:] = remaining
            warnings.warn(
                'Destructive tests are skipped in parallel mode.', stacklevel=2
            )
        elif getpass.getuser() not in ['lume', 'runner']:
            response = input(
                '\n\n\033[33mThere are destructive tests.\nTHIS MAY DELETE ALL OF YOUR HOMEBREW PACKAGES.\nDo you actually want to run them on current environment?\033[0m [y/N]: '
            )
            if response.lower() != 'y':
                config.hook.pytest_deselected(items=destructive)
                items[:] = remaining
                warnings.warn('Destructive tests are skipped.', stacklevel=2)
            else:
                response = input(
                    'Do you want to clean up the environment before each destructive test? [y/N]: '
                )
                if response.lower() != 'y':
                    config.destructive_clean = False  # ty: ignore[unresolved-attribute]
                    warnings.warn(
                        'Do not run cleanup before destructive tests. Some tests may fail.',
                        stacklevel=2,
                    )


@pytest.fixture(scope='session', autouse=True)
def check_brew(tmp_path_factory: pytest.TempPathFactory) -> None:
    for env in os.environ:
        if env.startswith('HOMEBREW_BREWFILE'):
            del os.environ[env]
    os.environ['HOMEBREW_API_AUTO_UPDATE_SECS'] = '100000'
    os.environ['HOMEBREW_AUTO_UPDATE_SECS'] = '100000'


@pytest.fixture
def bf_cmd() -> str:
    return str(Path(__file__).parent / 'brew_file.py')


@pytest.fixture
def helper() -> BrewHelper:
    # BrewHelper with default options
    return BrewFile({}).helper


@pytest.fixture
def brew_info() -> BrewInfo:
    file = 'BrewfileTest' if is_mac() else 'BrewfileTestLinux'
    # BrewInfo with default options and input file
    bf = BrewFile({'input': Path(__file__).parent / 'files' / file})
    return bf.brewinfo
