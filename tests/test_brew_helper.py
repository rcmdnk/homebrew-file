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


def test_get_formula_list(helper: BrewHelper) -> None:
    assert isinstance(helper.get_formula_list(), list)


def test_get_cask_list(helper: BrewHelper) -> None:
    if not is_mac():
        pytest.skip('only for mac')
    assert isinstance(helper.get_cask_list(), list)


def test_flatten_dict(helper: BrewHelper) -> None:
    nested_dict = {'a': {'b': 1, 'c': {'d': 2}}, 'e': 3, 'f': {'g': 4}}
    flat_dict = helper.flatten_dict(nested_dict)
    assert flat_dict == {'b': 1, 'd': 2, 'e': 3, 'g': 4}


def test_name_and_token_key(helper: BrewHelper) -> None:
    # Test with full_name=False
    helper.opt['full_name'] = False
    assert helper.name_key() == 'name'
    assert helper.token_key() == 'token'

    # Test with full_name=True
    helper.opt['full_name'] = True
    assert helper.name_key() == 'full_name'
    assert helper.token_key() == 'full_token'


def test_get_json_info(helper: BrewHelper) -> None:
    # Test valid package
    info = helper.get_json_info('git', True)
    assert isinstance(info, dict)
    assert 'formulae' in info

    # Test invalid package
    info = helper.get_json_info('nonexistent-package', False)
    assert isinstance(info, list)
    assert any(
        'No available formula with the name "nonexistent-package".' in line
        for line in info
    )


def test_get_each_type_info(helper: BrewHelper) -> None:
    # Test formulae
    formula_info = helper.get_each_type_info('formulae')
    assert isinstance(formula_info, dict)
    assert len(formula_info) > 0

    if is_mac():
        # Test casks
        cask_info = helper.get_each_type_info('casks')
        assert isinstance(cask_info, dict)
        assert len(cask_info) > 0


def test_get_packages(helper: BrewHelper) -> None:
    # Test formulae
    formulae = helper.get_packages('formulae')
    assert isinstance(formulae, list)
    assert len(formulae) > 0

    # Test caching
    assert helper.get_packages('formulae') is formulae

    if is_mac():
        # Test casks
        casks = helper.get_packages('casks')
        assert isinstance(casks, list)
        assert len(casks) > 0


def test_get_all_info(helper: BrewHelper) -> None:
    info = helper.get_all_info()
    assert 'formulae' in info
    assert 'casks' in info

    # Test caching
    assert helper.get_all_info() is info


class TestGetDesc:
    def test_formula(self, helper: BrewHelper) -> None:
        helper.info = {
            'formulae': {'git': {'desc': 'Distributed revision control system'}},
            'casks': {},
        }
        assert helper.get_desc('git', 'formulae') == 'Distributed revision control system'

    def test_cask(self, helper: BrewHelper) -> None:
        helper.info = {
            'formulae': {},
            'casks': {'firefox': {'desc': 'Web browser'}},
        }
        assert helper.get_desc('firefox', 'casks') == 'Web browser'

    def test_missing(self, helper: BrewHelper) -> None:
        helper.info = {'formulae': {}, 'casks': {}}
        assert helper.get_desc('nonexistent-package-xyz', 'formulae') == ''

    def test_none_desc(self, helper: BrewHelper) -> None:
        helper.info = {
            'formulae': {'git': {'desc': None}},
            'casks': {},
        }
        assert helper.get_desc('git', 'formulae') == ''

    def test_no_desc_key(self, helper: BrewHelper) -> None:
        helper.info = {
            'formulae': {'git': {'name': 'git'}},
            'casks': {},
        }
        assert helper.get_desc('git', 'formulae') == ''
