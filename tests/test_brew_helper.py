import logging
import subprocess
from pathlib import Path

import pytest

from . import brew_file


@pytest.fixture
def helper():
    bf = brew_file.BrewFile()
    return bf.helper


def test_readstdout(helper):
    proc = subprocess.Popen(
        ["printf", "abc\n def \n\nghi"],
        stdout=subprocess.PIPE,
        stderr=None,
        text=True,
    )
    results = ["abc", " def", "ghi"]
    for a, b in zip(helper.readstdout(proc), results):
        assert a == b


@pytest.mark.parametrize(
    "cmd, ret, lines, exit_on_err, separate_err, env",
    [
        ("echo test text", 0, ["test text"], True, False, None),
        (["echo", "test", "text"], 0, ["test text"], True, False, None),
        (
            "grep a no_such_file",
            2,
            ["grep: no_such_file: No such file or directory"],
            False,
            False,
            None,
        ),
        ("grep a no_such_file", 2, [], False, True, None),
        ("_wrong_command_ test", 2, None, False, False, None),
        (
            [f"{Path(__file__).parent}/scripts/proc_env_test.sh"],
            0,
            ["abc"],
            False,
            False,
            {"TEST_VAL": "abc"},
        ),
    ],
)
def test_proc(helper, cmd, ret, lines, exit_on_err, separate_err, env):
    ret_proc, lines_proc = helper.proc(
        cmd, exit_on_err=exit_on_err, separate_err=separate_err, env=env
    )
    assert ret_proc == ret
    if lines is not None:
        assert lines_proc == lines


@pytest.fixture
def err_cmd():
    cmd = {
        "ech test": {
            "ret": 2,
            "out": "[Errno 2] No such file or directory: 'ech'",
            "oserr": True,
        },
        "ls /path/to/not/exist": {
            "ret": 1 if brew_file.is_mac() else 2,
            "out": "ls: /path/to/not/exist: No such file or directory"
            if brew_file.is_mac()
            else "ls: cannot access '/path/to/not/exist': No such file or directory",
            "oserr": False,
        },
    }
    return cmd


def test_proc_err(helper, caplog, err_cmd, capfd):
    for cmd in err_cmd:
        caplog.clear()
        ret_proc, lines_proc = helper.proc(
            cmd, separate_err=False, exit_on_err=False
        )
        assert ret_proc == err_cmd[cmd]["ret"]
        assert lines_proc == [err_cmd[cmd]["out"]]
        assert caplog.record_tuples == [
            ("tests.brew_file", logging.INFO, f"$ {cmd}"),
            (
                "tests.brew_file",
                logging.INFO,
                f"{err_cmd[cmd]['out']}",
            ),
        ]
        out, err = capfd.readouterr()
        assert out == ""
        assert err == ""

    for cmd in err_cmd:
        caplog.clear()
        ret_proc, lines_proc = helper.proc(
            cmd, separate_err=True, exit_on_err=False
        )
        assert ret_proc == err_cmd[cmd]["ret"]
        assert lines_proc == []
        if err_cmd[cmd]["oserr"]:
            record = [
                ("tests.brew_file", logging.INFO, f"$ {cmd}"),
                ("tests.brew_file", logging.ERROR, err_cmd[cmd]["out"]),
            ]
            syserr = ""
        else:
            record = [("tests.brew_file", logging.INFO, f"$ {cmd}")]
            syserr = err_cmd[cmd]["out"] + "\n"
        assert caplog.record_tuples == record
        out, err = capfd.readouterr()
        assert out == ""
        assert err == syserr


def test_proc_err_exit_on_err(helper, caplog, err_cmd, capfd):
    for cmd in err_cmd:
        caplog.clear()
        with pytest.raises(brew_file.CmdError) as e:
            ret_proc, lines_proc = helper.proc(
                cmd,
                separate_err=False,
                print_err=True,
                exit_on_err=True,
            )
        assert e.type == brew_file.CmdError
        assert e.value.return_code == err_cmd[cmd]["ret"]
        assert (
            str(e.value) == f"Failed at command: {cmd}\n{err_cmd[cmd]['out']}"
        )
        assert caplog.record_tuples == [
            ("tests.brew_file", logging.INFO, f"$ {cmd}"),
            ("tests.brew_file", logging.INFO, err_cmd[cmd]["out"]),
        ]
        out, err = capfd.readouterr()
        assert out == ""
        assert err == ""

    for cmd in err_cmd:
        caplog.clear()
        with pytest.raises(brew_file.CmdError) as e:
            ret_proc, lines_proc = helper.proc(
                cmd,
                separate_err=True,
                print_err=True,
                exit_on_err=True,
            )

        if err_cmd[cmd]["oserr"]:
            record = [
                ("tests.brew_file", logging.INFO, f"$ {cmd}"),
                ("tests.brew_file", logging.ERROR, err_cmd[cmd]["out"]),
            ]
            syserr = ""
        else:
            record = [("tests.brew_file", logging.INFO, f"$ {cmd}")]
            syserr = err_cmd[cmd]["out"] + "\n"
        assert e.type == brew_file.CmdError
        assert e.value.return_code == err_cmd[cmd]["ret"]
        assert str(e.value) == f"Failed at command: {cmd}\n"
        assert caplog.record_tuples == record
        out, err = capfd.readouterr()
        assert out == ""
        assert err == syserr


def test_proc_dryrun(helper):
    ret_proc, lines_proc = helper.proc("echo test", dryrun=True)
    assert ret_proc == 0
    assert lines_proc == ["echo test"]


def test_brew_val(helper):
    prefix = Path(helper.proc("which brew")[1][0]).parents[1]
    assert helper.brew_val("prefix") == str(prefix)


def test_get_formula_list(helper, python):
    formula_list = helper.get_formula_list()
    assert "python@3.10" in formula_list


def test_get_cask_list(helper):
    if not brew_file.is_mac():
        pytest.skip("only for mac")
    assert isinstance(helper.get_cask_list(), list)


def test_get_info(helper, python):
    info = helper.get_info("python@3.10")
    assert info["python@3.10"]["installed"][0]["used_options"] == []


def test_get_installed(helper, python):
    installed = helper.get_installed("python@3.10")
    # brew version can contained additional number with '_'
    assert installed["version"].split("_")[0].startswith("3.10")


def test_get_option(helper, python):
    opt = helper.get_option("python@3.10")
    assert opt == ""


def test_get_formula_info(helper):
    info = helper.get_formula_info()
    assert "name" in info[0]
    assert "tap" in info[0]
    assert "aliases" in info[0]
    assert "linked_keg" in info[0]
    assert "installed" in info[0]


def test_get_formula_aliases(helper):
    aliases = helper.get_formula_aliases()
    assert aliases["python"].startswith("python@")


def test_get_tap_packs(helper, tap):
    packs = helper.get_tap_packs("rcmdnk/rcmdnkpac")
    assert "sentaku" in packs


def test_get_cask_info(helper):
    if not brew_file.is_mac():
        pytest.skip("only for mac")
    info = helper.get_cask_info()
    assert info[0]["tap"] == "homebrew/cask"


def test_get_tap_casks(helper, tap):
    if not brew_file.is_mac():
        pytest.skip("only for mac")
    casks = helper.get_tap_casks("rcmdnk/rcmdnkcask")
    assert "vem" in casks


def test_get_leaves(helper):
    pass
