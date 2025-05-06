from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Any

import pytest

from .brew_file import BrewFile, BrewHelper, CmdError, is_mac


@pytest.fixture
def helper() -> BrewHelper:
    bf = BrewFile()
    return bf.helper


def test_readstdout(helper: BrewHelper) -> None:
    proc = subprocess.Popen(
        ['printf', 'abc\n def \n\nghi'],
        stdout=subprocess.PIPE,
        stderr=None,
        text=True,
    )
    results = ['abc', ' def', 'ghi']
    for a, b in zip(helper.readstdout(proc), results):
        assert a == b


@pytest.mark.parametrize(
    ('cmd', 'ret', 'lines', 'exit_on_err', 'separate_err', 'env'),
    [
        ('echo test text', 0, ['test text'], True, False, None),
        (['echo', 'test', 'text'], 0, ['test text'], True, False, None),
        (
            'grep a no_such_file',
            2,
            ['grep: no_such_file: No such file or directory'],
            False,
            False,
            None,
        ),
        ('grep a no_such_file', 2, [], False, True, None),
        ('_wrong_command_ test', 2, None, False, False, None),
        (
            [f'{Path(__file__).parent}/scripts/proc_env_test.sh'],
            0,
            ['abc'],
            False,
            False,
            {'TEST_VAL': 'abc'},
        ),
    ],
)
def test_proc(
    helper: BrewHelper,
    cmd: str,
    ret: int,
    lines: list[str],
    exit_on_err: bool,
    separate_err: bool,
    env: dict | None,
) -> None:
    ret_proc, lines_proc = helper.proc(
        cmd,
        exit_on_err=exit_on_err,
        separate_err=separate_err,
        env=env,
    )
    assert ret_proc == ret
    if lines is not None:
        assert lines_proc == lines


@pytest.fixture
def err_cmd() -> dict[str, Any]:
    return {
        'ech test': {
            'ret': 2,
            'out': "[Errno 2] No such file or directory: 'ech'",
            'oserr': True,
        },
        'ls /path/to/not/exist': {
            'ret': 1 if is_mac() else 2,
            'out': (
                'ls: /path/to/not/exist: No such file or directory'
                if is_mac()
                else "ls: cannot access '/path/to/not/exist': No such file or directory"
            ),
            'oserr': False,
        },
    }


def test_proc_err(
    helper: BrewHelper,
    caplog: pytest.LogCaptureFixture,
    err_cmd: dict[str, Any],
    capfd: pytest.CaptureFixture,
) -> None:
    for cmd in err_cmd:
        caplog.clear()
        ret_proc, lines_proc = helper.proc(
            cmd,
            separate_err=False,
            exit_on_err=False,
        )
        assert ret_proc == err_cmd[cmd]['ret']
        assert lines_proc == [err_cmd[cmd]['out']]
        assert caplog.record_tuples == [
            ('tests.brew_file', logging.INFO, f'$ {cmd}'),
            (
                'tests.brew_file',
                logging.INFO,
                f'{err_cmd[cmd]["out"]}',
            ),
        ]
        out, err = capfd.readouterr()
        assert out == ''
        assert err == ''

    for cmd in err_cmd:
        caplog.clear()
        ret_proc, lines_proc = helper.proc(
            cmd,
            separate_err=True,
            exit_on_err=False,
        )
        assert ret_proc == err_cmd[cmd]['ret']
        assert lines_proc == []
        if err_cmd[cmd]['oserr']:
            record = [
                ('tests.brew_file', logging.INFO, f'$ {cmd}'),
                ('tests.brew_file', logging.ERROR, err_cmd[cmd]['out']),
            ]
            syserr = ''
        else:
            record = [('tests.brew_file', logging.INFO, f'$ {cmd}')]
            syserr = err_cmd[cmd]['out'] + '\n'
        assert caplog.record_tuples == record
        out, err = capfd.readouterr()
        assert out == ''
        assert err == syserr


def test_proc_err_exit_on_err(
    helper: BrewHelper,
    caplog: pytest.LogCaptureFixture,
    err_cmd: dict[str, Any],
    capfd: pytest.CaptureFixture,
) -> None:
    for cmd in err_cmd:
        caplog.clear()
        with pytest.raises(CmdError) as e:
            _ = helper.proc(
                cmd,
                separate_err=False,
                print_err=True,
                exit_on_err=True,
            )
        assert e.type == CmdError
        assert e.value.return_code == err_cmd[cmd]['ret']
        assert (
            str(e.value) == f'Failed at command: {cmd}\n{err_cmd[cmd]["out"]}'
        )
        assert caplog.record_tuples == [
            ('tests.brew_file', logging.INFO, f'$ {cmd}'),
            ('tests.brew_file', logging.INFO, err_cmd[cmd]['out']),
        ]
        out, err = capfd.readouterr()
        assert out == ''
        assert err == ''

    for cmd in err_cmd:
        caplog.clear()
        with pytest.raises(CmdError) as e:
            _ = helper.proc(
                cmd,
                separate_err=True,
                print_err=True,
                exit_on_err=True,
            )

        if err_cmd[cmd]['oserr']:
            record = [
                ('tests.brew_file', logging.INFO, f'$ {cmd}'),
                ('tests.brew_file', logging.ERROR, err_cmd[cmd]['out']),
            ]
            syserr = ''
        else:
            record = [('tests.brew_file', logging.INFO, f'$ {cmd}')]
            syserr = err_cmd[cmd]['out'] + '\n'
        assert e.type == CmdError
        assert e.value.return_code == err_cmd[cmd]['ret']
        assert str(e.value) == f'Failed at command: {cmd}\n'
        assert caplog.record_tuples == record
        out, err = capfd.readouterr()
        assert out == ''
        assert err == syserr


def test_proc_dryrun(helper: BrewHelper) -> None:
    ret_proc, lines_proc = helper.proc('echo test', dryrun=True)
    assert ret_proc == 0
    assert lines_proc == ['echo test']


def test_brew_val(helper: BrewHelper) -> None:
    prefix = Path(helper.proc('which brew')[1][0]).parents[1]
    assert helper.brew_val('prefix') == str(prefix)


def test_get_formula_list(helper: BrewHelper, python: str) -> None:
    formula_list = helper.get_formula_list()
    assert python in formula_list


def test_get_cask_list(helper: BrewHelper) -> None:
    if not is_mac():
        pytest.skip('only for mac')
    assert isinstance(helper.get_cask_list(), list)


def test_get_info(helper: BrewHelper, python: str) -> None:
    info = helper.get_info()['formulae'][python]
    assert info['installed'][0]['used_options'] == []


def test_get_installed(helper: BrewHelper, python: str) -> None:
    installed = helper.get_installed(python)
    # brew version can contained additional number with '_'
    assert installed['version'].split('_')[0].startswith(python.split('@')[1])


def test_get_option(helper: BrewHelper, python: str) -> None:
    opt = helper.get_option(python)
    assert opt == ''


def test_get_formula_info(helper: BrewHelper) -> None:
    info = next(iter(helper.get_info()['formulae'].values()))
    assert 'name' in info
    assert 'tap' in info
    assert 'aliases' in info
    assert 'linked_keg' in info
    assert 'installed' in info


def test_get_formula_aliases(helper: BrewHelper, python: str) -> None:
    aliases = helper.get_formula_aliases()
    assert aliases['homebrew/core']['python'].startswith('python@')


def test_get_tap_packs(helper: BrewHelper, tap: list[str]) -> None:
    packs = helper.get_tap_packs(tap[0])
    assert 'sentaku' in packs['formulae']


def test_get_cask_info(helper: BrewHelper) -> None:
    if not is_mac():
        pytest.skip('only for mac')
    info = list(helper.get_info()['casks'].values())
    if info:
        assert 'token' in info[0]
        assert 'tap' in info[0]
        assert 'old_tokens' in info[0]


def test_get_tap_casks(helper: BrewHelper, tap: list[str]) -> None:
    if not is_mac():
        pytest.skip('only for mac')
    casks = helper.get_tap_packs(tap[1])['casks']
    assert 'vem' in casks


def test_get_leaves(helper: BrewHelper) -> None:
    pass
