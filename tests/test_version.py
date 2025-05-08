from __future__ import annotations

import re
from pathlib import Path

from .brew_file import BrewHelper, __version__


def test_version() -> None:
    # Check if version in pyproject.toml matches the version in __version__
    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib
    with Path(Path(__file__).parents[1] / 'pyproject.toml').open('rb') as f:
        version = tomllib.load(f)['project']['version']
    assert version == __version__


def test_version_format() -> None:
    # Version should follow semantic versioning (MAJOR.MINOR.PATCH)
    assert re.match(r'^\d+\.\d+\.\d+$', __version__)


def test_version_command(bf_cmd: str, helper: BrewHelper) -> None:
    # Test version command output
    _, lines = helper.proc(f'"{bf_cmd}" version')
    assert any(__version__ in line for line in lines)
