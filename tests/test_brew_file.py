import subprocess
from pathlib import Path
from . import brew_file

import pytest


@pytest.fixture
def bf():
    obj = brew_file.BrewFile({})
    return obj


def test_parse_env_opts(bf):
    pass


def test_set_args(bf):
    pass


def test_ask_yn(bf):
    pass


def test_verbose(bf):
    pass


def test_proc(bf):
    pass


def test_remove(bf):
    pass


def test_brew_val(bf):
    pass


def test_read_all(bf):
    pass


def test_read(bf):
    pass


def test_list_to_main(bf):
    pass


def test_input_to_list(bf):
    pass


def test_write(bf):
    pass


def test_get(bf):
    pass


def test_remove_pack(bf):
    pass


def test_repo_name(bf):
    pass


def test_user_name(bf):
    pass


def test_input_dir(bf):
    pass


def test_input_file(bf):
    pass


def test_repo_file(bf):
    pass


def test_init_repo(bf):
    pass


def test_clone_repo(bf):
    pass


def test_check_github_repo(bf):
    pass


def test_check_local_repo(bf):
    pass


def test_check_repo(bf):
    pass


def test_check_gitconfig(bf):
    pass


def test_repomgr(bf):
    pass


def test_brew_cmd(bf):
    pass


def test_check_brwe_cmd(bf):
    pass


def test_check_mas_cmd(bf):
    pass


def test_get_appstore_list(bf):
    pass


def test_get_cask_list(bf):
    pass


def get_list(bf):
    pass


def clean_list(bf):
    pass


def input_backup(bf):
    pass


def set_brewfile_repo(bf):
    pass


def set_brewfile_local(bf):
    pass


def initialize(bf):
    pass


def initialize_write(bf):
    pass


def check_input_file(bf):
    pass


def get_files(bf):
    pass


def edit_brewfile(bf):
    pass


def cat_brewfile(bf):
    pass


def clean_non_request(bf):
    pass


def cleanup(bf):
    pass


def install(bf):
    pass


def find_app(bf):
    pass


def find_brew_app(bf):
    pass


def check_cask(bf):
    pass


def make_pack_deps(bf):
    pass


def my_test(bf):
    bf.my_test()


def execute(bf):
    pass
