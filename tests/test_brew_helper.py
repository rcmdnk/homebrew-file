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
        ("_wrong_command_ test", -1, None, False, False, None),
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


def test_proc_err(helper):
    with pytest.raises(SystemExit) as e:
        ret_proc, lines_proc = helper.proc("_wrong_command_", exit_on_err=True)
    assert e.type == SystemExit
    with pytest.raises(SystemExit) as e:
        ret_proc, lines_proc = helper.proc(
            "_wrong_command_", print_err=False, exit_on_err=True
        )
    assert e.type == SystemExit


def test_proc_exit_on_err(helper):
    ret_proc, lines_proc = helper.proc(
        "ech test", separate_err=False, exit_on_err=False
    )
    assert ret_proc == -1
    print(lines_proc)
    assert lines_proc == [
        "ech test: [Errno 2] No such file or directory: 'ech'"
    ]
    ret_proc, lines_proc = helper.proc(
        "ech test", separate_err=True, exit_on_err=False
    )
    assert ret_proc == -1
    print(lines_proc)
    assert lines_proc == [
        "ech test: [Errno 2] No such file or directory: 'ech'"
    ]


def test_proc_dryrun(helper):
    ret_proc, lines_proc = helper.proc("echo test", dryrun=True)
    assert ret_proc == 0
    assert lines_proc == ["echo test"]


def test_out(helper, capsys):
    helper.opt["verbose"] = 1
    helper.out("show", verbose=0)
    helper.out("no show", verbose=100)
    captured = capsys.readouterr()
    assert captured.out == "show\n"


def test_info(helper, capsys):
    helper.opt["verbose"] = 2
    helper.info("show")
    helper.opt["verbose"] = 1
    helper.info("no show")
    captured = capsys.readouterr()
    assert captured.out == "show\n"


def test_warn(helper, capsys):
    helper.opt["verbose"] = 1
    helper.warn("show")
    helper.opt["verbose"] = 0
    helper.warn("no show")
    captured = capsys.readouterr()
    assert captured.out == "[WARNING]: show\n"


def test_err(helper, capsys):
    helper.opt["verbose"] = 0
    helper.err("show")
    helper.opt["verbose"] = -1
    helper.err("no show")
    captured = capsys.readouterr()
    assert captured.out == "[ERROR]: show\n"


def test_banner(helper, capsys):
    helper.banner("test banner")
    captured = capsys.readouterr()
    assert captured.out == "\n###########\ntest banner\n###########\n\n"


def test_brew_val(helper):
    prefix = "/".join(helper.proc("which brew")[1][0].split("/")[:-2])
    assert helper.brew_val("prefix") == prefix
