from __future__ import annotations

import logging
import os
import platform
import sys
from pathlib import Path

import pytest

from .brew_file import (
    LogFormatter,
    expandpath,
    home_tilde,
    is_mac,
    shell_envs,
    to_bool,
    to_num,
)


def test_log_formatter() -> None:
    formatter = LogFormatter()
    record = logging.LogRecord(
        'test', logging.INFO, 'test.py', 1, 'test message', (), None
    )
    formatted = formatter.format(record)
    assert formatted == 'test message'

    # Test different log levels
    levels = [
        logging.DEBUG,
        logging.INFO,
        logging.WARNING,
        logging.ERROR,
        logging.CRITICAL,
    ]
    for level in levels:
        record = logging.LogRecord(
            'test', level, 'test.py', 1, 'test message', (), None
        )
        formatted = formatter.format(record)
        assert 'test message' in formatted


def test_is_mac(monkeypatch: pytest.MonkeyPatch) -> None:
    assert bool(sys.platform == 'darwin') == bool(is_mac())
    monkeypatch.setattr(platform, 'system', lambda: 'Darwin')
    assert is_mac()
    monkeypatch.setattr(platform, 'system', lambda: 'Linux')
    assert not is_mac()


@pytest.mark.parametrize(
    ('val', 'result'),
    [
        (True, True),
        (False, False),
        (0, False),
        (1, True),
        (10, True),
        ('True', True),
        ('true', True),
        ('false', False),
        ('others', False),
        ('1', True),
        ('0', False),
        ('', False),
    ],
)
def test_to_bool(val: bool | int | str, result: bool) -> None:
    ret = to_bool(val)
    assert isinstance(ret, bool)
    assert ret == result


@pytest.mark.parametrize(
    ('val', 'result'),
    [
        (True, 1),
        (False, 0),
        (1, 1),
        ('1', 1),
        ('01', 1),
        ('-2', -2),
        ('true', 1),
        ('false', 0),
        ('others', 0),
    ],
)
def test_to_num(val: bool | int | str, result: bool) -> None:
    ret = to_num(val)
    assert isinstance(ret, int)
    assert ret == result


@pytest.mark.parametrize(
    ('path', 'result'),
    [
        ('/normal/path', '/normal/path'),
        (
            '${HOSTNAME}/$HOSTTYPE/${OSTYPE}/$PLATFORM',
            f'{shell_envs["HOSTNAME"]}/{shell_envs["HOSTTYPE"]}/{shell_envs["OSTYPE"]}/{shell_envs["PLATFORM"]}',
        ),
        ('~/test', Path('~/test').expanduser()),
        ('$HOME/', Path('~/').expanduser()),
        ('${HOME}/', Path('~/').expanduser()),
    ],
)
def test_expandpath(path: str, result: str) -> None:
    assert expandpath(path) == Path(result)


def test_home_tilde() -> None:
    assert (
        home_tilde(Path(os.environ['HOME']) / 'test' / 'path') == '~/test/path'
    )
