from pathlib import Path

from . import brew_file


def test_version():
    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib
    with open(Path(__file__).parents[1] / "pyproject.toml", "rb") as f:
        version = tomllib.load(f)["project"]["version"]
    assert version == brew_file.__version__
