from pathlib import Path

import pytest

from . import brew_file


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


def test_read(bf, tmp_path):
    helper = brew_file.BrewHelper({})

    bf.brewinfo_ext = []
    path = Path(f"{Path(__file__).parent}/files/BrewfileMain")
    brewinfo = brew_file.BrewInfo(helper=helper, path=path)
    ret = bf.read(brewinfo, True)
    assert ret.path == path

    bf.brewinfo_ext = []
    path = Path(f"{Path(__file__).parent}/files/BrewfileMain")
    brewinfo = brew_file.BrewInfo(helper=helper, path=path)
    ret = bf.read(brewinfo, False)
    assert ret is None

    bf.brewinfo_ext = []
    path = Path(f"{Path(__file__).parent}/files/BrewfileTest")
    brewinfo = brew_file.BrewInfo(helper=helper, path=path)
    ret = bf.read(brewinfo, True)
    path = Path(f"{Path(__file__).parent}/files/BrewfileMain")
    assert ret.path == path
    files = [
        Path(f"{Path(__file__).parent}/files/BrewfileMain"),
        Path(f"{Path(__file__).parent}/files/BrewfileExt"),
        Path(f"{Path(__file__).parent}/files/BrewfileExt2"),
        Path(f"{Path(__file__).parent}/files/BrewfileExt3"),
        Path(f"{Path(__file__).parent}/files/BrewfileNotExist"),
        Path(Path("~/BrewfileHome").expanduser()),
    ]
    for i, f in zip(bf.brewinfo_ext, files):
        assert i.path == f

    # Absolute path check
    f1 = tmp_path / "f1"
    f2 = tmp_path / "f2"
    f3 = tmp_path / "f3"
    with open(f1, "w") as f:
        f.write(f"main {f2}")
    with open(f2, "w") as f:
        f.write(f"main {f3}")

    bf.brewinfo_ext = []
    brewinfo = brew_file.BrewInfo(helper=helper, path=f1)
    ret = bf.read(brewinfo, True)
    assert ret.path == Path(f3)


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
    bf.opt["repo"] = "git@github.com:abc/def.git"
    assert bf.repo_name() == "def"
    bf.opt["repo"] = "https://github.com/abc/def.git"
    assert bf.repo_name() == "def"


def test_user_name(bf):
    bf.opt["repo"] = "git@github.com:abc/def.git"
    assert bf.user_name() == "abc"
    bf.opt["repo"] = "https://github.com/abc/def.git"
    assert bf.user_name() == "abc"


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


def test_get_list(bf):
    pass


def test_clean_list(bf):
    pass


def test_input_backup(bf):
    pass


def test_set_brewfile_repo(bf):
    pass


def test_set_brewfile_local(bf):
    pass


def test_initialize(bf):
    pass


def test_initialize_write(bf):
    pass


def test_check_input_file(bf):
    pass


def test_get_files(bf):
    pass


def test_edit_brewfile(bf):
    pass


def test_cat_brewfile(bf):
    pass


def test_clean_non_request(bf):
    pass


def test_cleanup(bf):
    pass


def test_install(bf):
    pass


def test_find_app(bf):
    pass


def test_find_brew_app(bf):
    pass


def test_check_cask(bf):
    pass


def test_make_pack_deps(bf):
    pass


def test_my_test(bf):
    bf.my_test()


def test_execute(bf):
    pass
