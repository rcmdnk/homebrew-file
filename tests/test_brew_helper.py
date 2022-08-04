import subprocess
from pathlib import Path
from . import brew_file

import pytest


@pytest.fixture
def helper():
    obj = brew_file.BrewHelper({})
    return obj


def test_readstdout(helper):
    proc = subprocess.Popen(
        ['printf', 'abc\n def \n\nghi'],
        stdout=subprocess.PIPE, stderr=None, text=True)
    results = ['abc', ' def', 'ghi']
    for a, b in zip(helper.readstdout(proc), results):
        assert a == b


@pytest.mark.parametrize(
    "cmd, ret, lines, exit_on_err, separate_err, env",
    [
        ("echo test text", 0, ["test text"], True, False, None),
        (["echo", "test", "text"], 0, ["test text"], True, False, None),
        ("grep a no_such_file", 2, ["grep: no_such_file: No such file or directory"], False, False, None),
        ("grep a no_such_file", 2, [], False, True, None),
        ("_wrong_command_ test", -1, None, False, False, None),
        ([f"{Path(__file__).parent}/scripts/proc_env_test.sh"], 0, ['abc'], False, False, {'TEST_VAL': 'abc'}),
    ]
)
def test_proc(helper, cmd, ret, lines, exit_on_err, separate_err, env):
    ret_proc, lines_proc = helper.proc(cmd, exit_on_err=exit_on_err, separate_err=separate_err, env=env)
    assert ret_proc == ret
    if lines is not None:
        assert lines_proc == lines


def test_proc_err(helper):
    with pytest.raises(SystemExit) as e:
        ret_proc, lines_proc = helper.proc("_wrong_command_", exit_on_err=True)
    assert e.type == SystemExit


def test_brew_val(helper):
    prefix = '/'.join(helper.proc('which brew')[1][0].split('/')[:-2])
    assert helper.brew_val('prefix') == prefix
