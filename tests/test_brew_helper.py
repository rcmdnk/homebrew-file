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
        },
        "ls /path/to/not/exist": {
            "ret": 1 if brew_file.is_mac() else 2,
            "out": "ls: /path/to/not/exist: No such file or directory"
            if brew_file.is_mac()
            else "ls: cannot access '/path/to/not/exist': No such file or directory",
        },
    }
    return cmd


def test_proc_err(helper, caplog, err_cmd):
    caplog.set_level(logging.DEBUG)

    for cmd in err_cmd:
        caplog.clear()
        ret_proc, lines_proc = helper.proc(
            cmd, separate_err=False, exit_on_err=False
        )
        assert ret_proc == err_cmd[cmd]["ret"]
        assert lines_proc == [err_cmd[cmd]["out"]]

    for cmd in err_cmd:
        caplog.clear()
        ret_proc, lines_proc = helper.proc(
            cmd, separate_err=True, exit_on_err=False
        )
        assert ret_proc == err_cmd[cmd]["ret"]
        assert lines_proc == []
        assert caplog.record_tuples == [
            ("tests.brew_file", logging.INFO, f"$ {cmd}"),
            ("tests.brew_file", logging.INFO, ""),
            (
                "tests.brew_file",
                logging.ERROR,
                f"{err_cmd[cmd]['out']}\n",
            ),
        ]


def test_proc_err_exit_on_err(helper, capsys, err_cmd):
    for cmd in err_cmd:
        with pytest.raises(brew_file.CmdError) as e:
            ret_proc, lines_proc = helper.proc(
                cmd,
                separate_err=False,
                print_err=True,
                exit_on_err=True,
            )
        assert e.type == brew_file.CmdError
        assert e.value.return_code == err_cmd[cmd]["ret"]
        assert str(e.value) == f"{err_cmd[cmd]['out']}\n"

    for cmd in err_cmd:
        with pytest.raises(brew_file.CmdError) as e:
            ret_proc, lines_proc = helper.proc(
                cmd,
                separate_err=True,
                print_err=True,
                exit_on_err=True,
            )
        assert e.type == brew_file.CmdError
        assert e.value.return_code == err_cmd[cmd]["ret"]
        assert str(e.value) == f"{err_cmd[cmd]['out']}\n"


def test_proc_dryrun(helper):
    ret_proc, lines_proc = helper.proc("echo test", dryrun=True)
    assert ret_proc == 0
    assert lines_proc == ["echo test"]


def test_brew_val(helper):
    prefix = Path(helper.proc("which brew")[1][0]).parents[1]
    assert helper.brew_val("prefix") == str(prefix)


def test_get_info(helper, python):
    info = helper.get_info("python@3.10")
    assert info["python@3.10"]["installed"][0]["used_options"] == []


def test_get_tap_packs(helper, tap):
    packs = helper.get_tap_packs("rcmdnk/rcmdnkpac")
    assert "sentaku" in packs


def test_get_tap_casks(helper, tap):
    casks = helper.get_tap_casks("rcmdnk/rcmdnkcask")
    assert "vem" in casks
