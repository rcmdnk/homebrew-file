from __future__ import annotations

import os
import platform
import sys
from pathlib import Path

import pytest

from . import brew_file


def test_is_mac(monkeypatch: pytest.MonkeyPatch) -> None:
    assert bool(sys.platform == 'darwin') == bool(brew_file.is_mac())
    monkeypatch.setattr(platform, 'system', lambda: 'Darwin')
    assert brew_file.is_mac()
    monkeypatch.setattr(platform, 'system', lambda: 'Linux')
    assert not brew_file.is_mac()


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
    ret = brew_file.to_bool(val)
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
    ret = brew_file.to_num(val)
    assert isinstance(ret, int)
    assert ret == result


@pytest.mark.parametrize(
    ('path', 'result'),
    [
        ('/normal/path', '/normal/path'),
        (
            '${HOSTNAME}/$HOSTTYPE/${OSTYPE}/$PLATFORM',
            f'{brew_file.shell_envs["HOSTNAME"]}/{brew_file.shell_envs["HOSTTYPE"]}/{brew_file.shell_envs["OSTYPE"]}/{brew_file.shell_envs["PLATFORM"]}',
        ),
        ('~/test', Path('~/test').expanduser()),
        ('$HOME/', Path('~/').expanduser()),
        ('${HOME}/', Path('~/').expanduser()),
    ],
)
def test_expandpath(path: str, result: str) -> None:
    assert brew_file.expandpath(path) == Path(result)


def test_home_tilde() -> None:
    assert (
        brew_file.home_tilde(Path(os.environ['HOME']) / 'test' / 'path')
        == '~/test/path'
    )
