from __future__ import annotations

from pathlib import Path

from . import brew_file


def test_version() -> None:
    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib
    with Path(Path(__file__).parents[1] / 'pyproject.toml').open('rb') as f:
        version = tomllib.load(f)['project']['version']
    assert version == brew_file.__version__
