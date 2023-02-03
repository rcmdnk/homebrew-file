import logging
import subprocess
from pathlib import Path

import pytest

from . import brew_file


@pytest.fixture
def helper():
    obj = brew_file.BrewHelper({})
    return obj


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


def test_proc_err(helper, caplog):
    caplog.set_level(logging.DEBUG)

    caplog.clear()
    ret_proc, lines_proc = helper.proc(
        "ech test", separate_err=False, exit_on_err=False
    )
    assert ret_proc == 2
    assert lines_proc == ["[Errno 2] No such file or directory: 'ech'"]

    caplog.clear()
    ret_proc, lines_proc = helper.proc(
        "ls /path/to/not/exist", separate_err=False, exit_on_err=False
    )
    assert ret_proc == 1
    assert lines_proc == ["ls: /path/to/not/exist: No such file or directory"]

    caplog.clear()
    ret_proc, lines_proc = helper.proc(
        "ech test", separate_err=True, exit_on_err=False
    )
    assert ret_proc == 2
    assert lines_proc == []
    assert caplog.record_tuples == [
        ("tests.brew_file", logging.INFO, "$ ech test"),
        ("tests.brew_file", logging.INFO, ""),
        (
            "tests.brew_file",
            logging.ERROR,
            "[Errno 2] No such file or directory: 'ech'\n",
        ),
    ]

    caplog.clear()
    ret_proc, lines_proc = helper.proc(
        "ls /path/to/not/exist", separate_err=True, exit_on_err=False
    )
    assert ret_proc == 1
    assert lines_proc == []
    assert caplog.record_tuples == [
        ("tests.brew_file", logging.INFO, "$ ls /path/to/not/exist"),
        ("tests.brew_file", logging.INFO, ""),
        (
            "tests.brew_file",
            logging.ERROR,
            "ls: /path/to/not/exist: No such file or directory\n",
        ),
    ]


def test_proc_err_exit_on_err(helper, capsys):
    with pytest.raises(brew_file.CmdError) as e:
        ret_proc, lines_proc = helper.proc(
            "_wrong_command_",
            separate_err=False,
            print_err=True,
            exit_on_err=True,
        )
    assert e.type == brew_file.CmdError
    assert e.value.return_code == 2
    assert (
        str(e.value)
        == "[Errno 2] No such file or directory: '_wrong_command_'\n"
    )

    with pytest.raises(brew_file.CmdError) as e:
        ret_proc, lines_proc = helper.proc(
            "ls /path/to/not/exist",
            separate_err=False,
            print_err=True,
            exit_on_err=True,
        )
    assert e.type == brew_file.CmdError
    assert e.value.return_code == 1
    assert (
        str(e.value) == "ls: /path/to/not/exist: No such file or directory\n"
    )

    with pytest.raises(brew_file.CmdError) as e:
        ret_proc, lines_proc = helper.proc(
            "_wrong_command_",
            separate_err=True,
            print_err=True,
            exit_on_err=True,
        )
    assert e.type == brew_file.CmdError
    assert e.value.return_code == 2
    assert (
        str(e.value)
        == "[Errno 2] No such file or directory: '_wrong_command_'\n"
    )

    with pytest.raises(brew_file.CmdError) as e:
        ret_proc, lines_proc = helper.proc(
            "ls /path/to/not/exist",
            separate_err=True,
            print_err=True,
            exit_on_err=True,
        )
    assert e.type == brew_file.CmdError
    assert e.value.return_code == 1
    assert (
        str(e.value) == "ls: /path/to/not/exist: No such file or directory\n"
    )


def test_proc_dryrun(helper):
    ret_proc, lines_proc = helper.proc("echo test", dryrun=True)
    assert ret_proc == 0
    assert lines_proc == ["echo test"]


def test_banner(helper, caplog):
    caplog.set_level(logging.DEBUG)
    helper.banner("test banner")
    assert caplog.record_tuples == [
        (
            "tests.brew_file",
            logging.INFO,
            "\n###########\ntest banner\n###########\n",
        )
    ]


def test_brew_val(helper):
    prefix = "/".join(helper.proc("which brew")[1][0].split("/")[:-2])
    assert helper.brew_val("prefix") == prefix
