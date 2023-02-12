import io
import logging
import os
from pathlib import Path

import pytest

from . import brew_file


@pytest.fixture
def bf(caplog):
    caplog.set_level(logging.DEBUG)
    obj = brew_file.BrewFile({})
    return obj


def test_parse_env_opts(bf):
    os.environ["TEST_OPT"] = "--opt2=3 --opt3 opt4=4"
    opts = bf.parse_env_opts("TEST_OPT", {"--opt1": "1", "--opt2": "2"})
    assert opts == {"--opt1": "1", "--opt2": "3", "--opt3": "", "opt4": "4"}


def test_set_args(bf):
    bf.opt["appstore"] = 1
    bf.opt["no_appstore"] = 1
    bf.set_args(a="1", verbose="1")
    assert bf.opt["a"] == "1"
    assert bf.opt["verbose"] == "info"
    assert bf.opt["appstore"] == 1
    bf.opt["appstore"] = -1
    bf.opt["no_appstore"] = False
    bf.set_args()
    assert bf.opt["appstore"] == 1
    bf.opt["appstore"] = -1
    bf.opt["no_appstore"] = True
    bf.set_args()
    assert bf.opt["appstore"] == 0
    bf.opt["appstore"] = 1
    bf.opt["no_appstore"] = False
    bf.set_args()
    assert bf.opt["appstore"] == 1


@pytest.mark.parametrize(
    "input_value, ret, out",
    [
        ("y\n", True, "Question? [y/n]: "),
        ("Y\n", True, "Question? [y/n]: "),
        ("yes\n", True, "Question? [y/n]: "),
        ("YES\n", True, "Question? [y/n]: "),
        ("Yes\n", True, "Question? [y/n]: "),
        ("n\n", False, "Question? [y/n]: "),
        ("N\n", False, "Question? [y/n]: "),
        ("no\n", False, "Question? [y/n]: "),
        ("NO\n", False, "Question? [y/n]: "),
        ("No\n", False, "Question? [y/n]: "),
        (
            "a\nb\ny\n",
            True,
            "Question? [y/n]: Answer with yes (y) or no (n): Answer with yes (y) or no (n): ",
        ),
    ],
)
def test_ask_yn(bf, capsys, monkeypatch, input_value, ret, out):
    monkeypatch.setattr("sys.stdin", io.StringIO(input_value))
    assert bf.ask_yn("Question?") == ret
    captured = capsys.readouterr()
    assert captured.out == out


def test_ask_yn_y(bf, caplog):
    bf.opt["yn"] = True
    assert bf.ask_yn("Question?")
    assert caplog.record_tuples == [
        ("tests.brew_file", logging.INFO, "Question? [y/n]: y")
    ]


def test_banner(bf, caplog):
    bf.banner("test banner")
    assert caplog.record_tuples == [
        (
            "tests.brew_file",
            logging.INFO,
            "\n###########\ntest banner\n###########\n",
        )
    ]


def test_dryrun_banner(bf, caplog):
    bf.opt["dryrun"] = False
    with bf.DryrunBanner(bf):
        bf.log.info("test")
    assert caplog.record_tuples == [
        (
            "tests.brew_file",
            logging.INFO,
            "test",
        ),
    ]
    caplog.clear()
    bf.opt["dryrun"] = True
    with bf.DryrunBanner(bf):
        bf.log.info("test")
    assert caplog.record_tuples == [
        (
            "tests.brew_file",
            logging.INFO,
            "\n##################\n# This is dry run.\n##################\n",
        ),
        (
            "tests.brew_file",
            logging.INFO,
            "test",
        ),
        (
            "tests.brew_file",
            logging.INFO,
            "\n##################\n# This is dry run.\n##################\n",
        ),
    ]


def test_read_all(bf, tap):
    parent = Path(__file__).parent / "files"
    file = parent / "BrewfileTest"
    bf.set_input(file)
    bf.read_all()
    assert bf.brewinfo_main.file == parent / "BrewfileMain"
    assert [x.file for x in bf.brewinfo_ext] == [
        parent / x
        for x in [
            "BrewfileTest",
            "BrewfileExt",
            "BrewfileExt2",
            "BrewfileExt3",
            "BrewfileNotExist",
        ]
    ] + [Path(os.environ["HOME"]) / "BrewfileHomeForTestingNotExists"]
    assert bf.get("brew_input") == {
        "cmake",
        "ec2",
        "escape_sequence",
        "evernote_mail",
        "gcp-tools",
        "gmail_filter_manager",
        "gtask",
        "inputsource",
        "multi_clipboard",
        "open_newtab",
        "parse-plist",
        "po",
        "python@3.10",
        "rcmdnk-sshrc",
        "rcmdnk-trash",
        "screenutf8",
        "sd_cl",
        "sentaku",
        "shell-explorer",
        "shell-logger",
        "smenu",
        "stow_reset",
        "vim",
    }
    assert bf.get("brew_input_opt") == {
        "cmake": "",
        "ec2": "",
        "escape_sequence": "",
        "evernote_mail": "",
        "gcp-tools": "",
        "gmail_filter_manager": "",
        "gtask": "",
        "inputsource": "",
        "multi_clipboard": "",
        "open_newtab": "",
        "parse-plist": "",
        "po": "",
        "python@3.10": "",
        "rcmdnk-sshrc": "",
        "rcmdnk-trash": "",
        "screenutf8": "",
        "sd_cl": "",
        "sentaku": "",
        "shell-explorer": "",
        "shell-logger": "",
        "smenu": "",
        "stow_reset": "",
        "vim": " --HEAD",
    }
    assert bf.get("tap_input") == {
        "direct",
        "homebrew/cask",
        "homebrew/core",
        "rcmdnk/rcmdnkcask",
        "rcmdnk/rcmdnkpac",
    }
    assert bf.get("cask_input") == {"iterm2", "font-migu1m"}
    assert bf.get("appstore_input") == {"Keynote"}
    assert bf.get("main_input") == {"BrewfileMain"}
    assert bf.get("file_input") == {
        "BrewfileMain",
        "BrewfileExt",
        "BrewfileExt2",
        "BrewfileNotExist",
        "~/BrewfileHomeForTestingNotExists",
        "BrewfileExt3",
    }
    assert bf.get("before_input") == {"echo before", "echo EXT before"}
    assert bf.get("after_input") == {"echo after", "echo EXT after"}
    assert bf.get("cmd_input") == {"echo BrewfileMain", "echo other commands"}


def test_read(bf, tmp_path):
    helper = brew_file.BrewHelper({})

    bf.brewinfo_ext = []
    file = Path(f"{Path(__file__).parent}/files/BrewfileMain")
    brewinfo = brew_file.BrewInfo(helper=helper, file=file)
    ret = bf.read(brewinfo, True)
    assert ret.file == file

    bf.brewinfo_ext = []
    file = Path(f"{Path(__file__).parent}/files/BrewfileMain")
    brewinfo = brew_file.BrewInfo(helper=helper, file=file)
    ret = bf.read(brewinfo, False)
    assert ret is None

    bf.brewinfo_ext = []
    file = Path(f"{Path(__file__).parent}/files/BrewfileTest")
    brewinfo = brew_file.BrewInfo(helper=helper, file=file)
    ret = bf.read(brewinfo, True)
    file = Path(f"{Path(__file__).parent}/files/BrewfileMain")
    assert ret.file == file
    files = [
        Path(f"{Path(__file__).parent}/files/BrewfileMain"),
        Path(f"{Path(__file__).parent}/files/BrewfileExt"),
        Path(f"{Path(__file__).parent}/files/BrewfileExt2"),
        Path(f"{Path(__file__).parent}/files/BrewfileExt3"),
        Path(f"{Path(__file__).parent}/files/BrewfileNotExist"),
        Path(Path("~/BrewfileHomeForTestingNotExists").expanduser()),
    ]
    for i, f in zip(bf.brewinfo_ext, files):
        assert i.file == f

    # Absolute path check
    f1 = tmp_path / "f1"
    f2 = tmp_path / "f2"
    f3 = tmp_path / "f3"
    with open(f1, "w") as f:
        f.write(f"main {f2}")
    with open(f2, "w") as f:
        f.write(f"main {f3}")

    bf.brewinfo_ext = []
    brewinfo = brew_file.BrewInfo(helper=helper, file=f1)
    ret = bf.read(brewinfo, True)
    assert ret.file == Path(f3)


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


def test_add_path(bf):
    pass


def test_which_brew(bf):
    pass


def test_check_brew_cmd(bf):
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


def test_check_cask(bf, caplog, tmp_path):
    os.chdir(tmp_path)
    if not brew_file.is_mac():
        with pytest.raises(RuntimeError) as excinfo:
            bf.check_cask()
            assert str(excinfo.value) == "Cask is not available on Linux!"
        return
    bf.check_cask()
    assert "# Starting to check applications for Cask..." in caplog.messages[0]
    assert "# Summary" in "".join(caplog.messages)
    assert Path("Caskfile").exists()
    with open("Caskfile", "r") as f:
        lines = f.readlines()
    assert lines[0] == "# Cask applications\n"
    assert (
        lines[1]
        == "# Please copy these lines to your Brewfile and use with `brew-file install`.\n"
    )


def test_make_pack_deps(bf):
    pass


@pytest.fixture
def execute_fixture(monkeypatch) -> None:
    for func in [
        "check_brew_cmd",
        "check_cask",
        "set_brewfile_repo",
        "set_brewfile_local",
        "check_repo",
        "repomgr",
        "brew_cmd",
        "initialize",
        "check_input_file",
        "edit_brewfile",
        "cat_brewfile",
        "get_files",
        "clean_non_request",
        "cleanup",
        "install",
    ]:

        def set_func(func):
            # make local variable, needed to keep in print view
            name = func
            monkeypatch.setattr(
                brew_file.BrewFile,
                func,
                lambda self, *args, **kw: print(name, args, kw),  # noqa: T201
            )

        set_func(func)
    monkeypatch.setattr(
        brew_file.BrewFile, "check_brew_cmd", lambda self: None
    )
    monkeypatch.setattr(brew_file.BrewHelper, "brew_val", lambda self, x: x)
    monkeypatch.setattr(
        brew_file.BrewHelper,
        "proc",
        lambda self, *args, **kw: print("proc", args, kw),  # noqa: T201
    )
    bf = brew_file.BrewFile({})
    return bf


@pytest.mark.parametrize(
    "command, out",
    [
        ("casklist", "check_cask () {}\n"),  # noqa: P103
        ("set_repo", "set_brewfile_repo () {}\n"),  # noqa: P103
        ("set_local", "set_brewfile_local () {}\n"),  # noqa: P103
        ("pull", "check_repo () {}\nrepomgr ('pull',) {}\n"),  # noqa: P103
        ("push", "check_repo () {}\nrepomgr ('push',) {}\n"),  # noqa: P103
        ("brew", "check_repo () {}\nbrew_cmd () {}\n"),  # noqa: P103
        ("init", "check_repo () {}\ninitialize () {}\n"),  # noqa: P103
        ("dump", "check_repo () {}\ninitialize () {}\n"),  # noqa: P103
        (
            "edit",
            "check_repo () {}\ncheck_input_file () {}\nedit_brewfile () {}\n",  # noqa: P103
        ),
        (
            "cat",
            "check_repo () {}\ncheck_input_file () {}\ncat_brewfile () {}\n",  # noqa: P103
        ),
        (
            "get_files",
            "check_repo () {}\ncheck_input_file () {}\nget_files () {'is_print': True, 'all_files': False}\n",  # noqa: P103
        ),
        (
            "clean_non_request",
            "check_repo () {}\ncheck_input_file () {}\nclean_non_request () {}\n",  # noqa: P103
        ),
        (
            "clean",
            "check_repo () {}\ncheck_input_file () {}\ncleanup () {}\n",  # noqa: P103
        ),
    ],
)
def test_execute(execute_fixture, capsys, command, out):
    bf = execute_fixture
    bf.opt["command"] = command
    bf.execute()
    captured = capsys.readouterr()
    assert captured.out == out


def test_execute_update(execute_fixture, capsys):
    bf = execute_fixture
    bf.opt["command"] = "update"
    bf.execute()
    captured = capsys.readouterr()
    if brew_file.is_mac():
        assert (
            captured.out
            == "check_repo () {}\ncheck_input_file () {}\nproc ('brew update',) {'dryrun': False}\nproc ('brew upgrade --fetch-HEAD',) {'dryrun': False}\nproc ('brew upgrade --cask',) {'dryrun': False}\ninstall () {}\ncleanup () {}\ninitialize () {'check': False}\n"  # noqa: P103
        )
    else:
        assert (
            captured.out
            == "check_repo () {}\ncheck_input_file () {}\nproc ('brew update',) {'dryrun': False}\nproc ('brew upgrade --fetch-HEAD',) {'dryrun': False}\ninstall () {}\ncleanup () {}\ninitialize () {'check': False}\n"  # noqa: P103
        )


def test_execute_err(execute_fixture):
    bf = execute_fixture
    bf.opt["command"] = "wrong_command"
    with pytest.raises(RuntimeError) as excinfo:
        bf.execute()
    assert (
        str(excinfo.value)
        == f"Wrong command: wrong_command\nExecute `{brew_file.__prog__} help` for more information."
    )
