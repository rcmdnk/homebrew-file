import subprocess
from pathlib import Path
from . import brew_file

import pytest


@pytest.fixture
def brew_info():
    helper = brew_file.BrewHelper({})
    info = brew_file.BrewInfo(helper=helper, filename=f"{Path(__file__).parent}/files/BrewfileTest")
    return info


def test_get_dir(brew_info):
    assert brew_info.get_dir() == Path(f"{Path(__file__).parent}/files")


def test_check_file(brew_info):
    assert brew_info.check_file()
    info = brew_file.BrewInfo(helper=brew_info.helper, filename="not_exist")
    assert not info.check_file()


def test_check_dir(brew_info):
    assert brew_info.check_dir()
    info = brew_file.BrewInfo(helper=brew_info.helper, filename="/not/exist")
    assert not info.check_dir()


def test_clear(brew_info):
    pass


def test_clear_input(brew_info):
    pass


def test_clear_list(brew_info):
    pass


def test_input_to_list(brew_info):
    pass


def test_sort(brew_info):
    pass


def test_get(brew_info):
    pass


def test_get_files(brew_info):
    pass


def test_remove(brew_info):
    pass


def test_set_val(brew_info):
    pass


def test_add(brew_info):
    pass


def test_read(brew_info):
    pass


def test_get_tap_path(brew_info):
    tap_path = brew_info.get_tap_path("homebrew/core")
    assert tap_path.exists()


def test_get_tap_packs(brew_info):
    packs = brew_info.get_tap_packs("homebrew/core")
    assert type(packs) == list


def test_get_leaves(brew_info):
    pass


def test_get_info(brew_info):
    pass


def test_get_installed(brew_info):
    pass


def test_get_option(brew_info):
    pass


def test_convert_option(brew_info):
    pass


def test_packout(brew_info):
    pass


def test_mas_pack(brew_info):
    pass


def write(brew_info):
    pass
