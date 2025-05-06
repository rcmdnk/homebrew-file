# ruff: noqa: S605
from __future__ import annotations

import getpass
import os
import sys
from pathlib import Path
from typing import Any

import pytest

from .brew_file import BrewHelper

# DO NOT run this test in your local environment.
# Tests using the system Homebrew environment.
# They remove all packages at the beginning.

pytestmark = pytest.mark.serial


if sys.platform != 'darwin':
    pytest.skip('skipping macOS tests', allow_module_level=True)


if getpass.getuser() not in ['lume', 'runner']:
    pytest.skip(
        "skipping tests only for environments of lume's VM or GitHub Actions",
        allow_module_level=True,
    )


@pytest.fixture
def helper() -> BrewHelper:
    return BrewHelper()


@pytest.fixture(autouse=True)
def clean() -> None:
    clean_script = Path(__file__).parent / 'scripts' / 'clean_homebrew.sh'
    os.system(f'"{clean_script}"')


@pytest.fixture
def cmd() -> str:
    return str(Path(__file__).parent / 'brew_file.py')


@pytest.fixture
def brewfile(tmp_path: Path) -> str:
    return tmp_path / 'Brewfile'


@pytest.fixture
def backup(tmp_path: Path) -> str:
    return tmp_path / 'Brewfile.bak'


@pytest.fixture
def tmp_log(tmp_path: Path) -> str:
    return tmp_path / 'log'


def test_init(
    cmd: str, brewfile: str, helper: BrewHelper, backup: Path, tmp_path: Path
) -> None:
    # Test with no packages
    helper.proc(f'"{cmd}" init -f "{brewfile}" -y --no-repo')
    with Path(brewfile).open('r') as f:
        assert (
            f.read()
            == """
# tap repositories and their packages

tap homebrew/core

tap homebrew/cask
"""
        )

    # Test with some packages, with backup
    helper.proc('brew install brotli')
    helper.proc('brew install node')
    helper.proc('brew install rapidapi')
    helper.proc(f'"{cmd}" init -f "{brewfile}" -y -b {backup}')
    with Path(brewfile).open('r') as f:
        assert (
            f.read()
            == """
# tap repositories and their packages

tap homebrew/core
brew brotli
brew c-ares
brew ca-certificates
brew icu4c@77
brew libnghttp2
brew libuv
brew node
brew openssl@3

tap homebrew/cask
cask rapidapi
"""
        )
    with Path(f'{backup}').open('r') as f:
        assert (
            f.read()
            == """
# tap repositories and their packages

tap homebrew/core

tap homebrew/cask
"""
        )

    # test with --caskonly
    helper.proc(f'"{cmd}" init -f "{brewfile}" -y --caskonly')
    with Path(brewfile).open('r') as f:
        assert (
            f.read()
            == """
# tap repositories and their packages

tap homebrew/cask
cask rapidapi
"""
        )

    # Test with --on-request
    helper.proc(f'"{cmd}" init -f "{brewfile}" -y --on-request')
    with Path(brewfile).open('r') as f:
        assert (
            f.read()
            == """
# tap repositories and their packages

tap homebrew/core
brew brotli
brew node

tap homebrew/cask
cask rapidapi
"""
        )

    # Test with --top-packages
    helper.proc(
        f'"{cmd}" init -f "{brewfile}" -y --on-request --top-packages c-ares,libuv'
    )
    with Path(brewfile).open('r') as f:
        assert (
            f.read()
            == """
# tap repositories and their packages

tap homebrew/core
brew brotli
brew c-ares
brew libuv
brew node

tap homebrew/cask
cask rapidapi
"""
        )

    # Test with --leaves
    helper.proc(f'"{cmd}" init -f "{brewfile}" -y --leaves')
    with Path(brewfile).open('r') as f:
        assert (
            f.read()
            == """
# tap repositories and their packages

tap homebrew/core
brew node

tap homebrew/cask
cask rapidapi
"""
        )

    # Test with format
    helper.proc(f'"{cmd}" init -f "{brewfile}" -y --leaves -F bundle')
    with Path(brewfile).open('r') as f:
        assert (
            f.read()
            == """
# tap repositories and their packages

tap 'homebrew/core'
brew 'node'

tap 'homebrew/cask'
cask 'rapidapi'
"""
        )

    helper.proc(f'"{cmd}" init -f "{brewfile}" -y --leaves -F cmd')
    with Path(brewfile).open('r') as f:
        assert (
            f.read()
            == """#!/usr/bin/env bash

#BREWFILE_IGNORE
if ! which brew >& /dev/null;then
  brew_installed=0
  echo Homebrew is not installed!
  echo Install now...
  echo /bin/bash -c \\"\\$\\(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh\\)\\"
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"
  echo
fi
#BREWFILE_ENDIGNORE


# tap repositories and their packages

brew tap homebrew/core
brew install node

brew tap homebrew/cask
brew install rapidapi
"""
        )

    helper.proc(f'"{cmd}" init -f "{brewfile}" -y --leaves -F file')
    with Path(brewfile).open('r') as f:
        assert (
            f.read()
            == """
# tap repositories and their packages

tap homebrew/core
brew node

tap homebrew/cask
cask rapidapi
"""
        )

    # Test with oldnames and old_tokens
    with Path(brewfile).open('r') as f:
        content = f.read()
    content = content.replace('brew node', 'brew corepack')
    content = content.replace('cask rapidapi', 'cask paw')
    with Path(brewfile).open('w') as f:
        f.write(content)
    helper.proc(f'"{cmd}" init -f "{brewfile}" -y --leaves')
    with Path(brewfile).open('r') as f:
        assert (
            f.read()
            == """
# tap repositories and their packages

tap homebrew/core
brew corepack

tap homebrew/cask
cask paw
"""
        )

    # Test with aliases
    with Path(brewfile).open('r') as f:
        content = f.read()
    content = content.replace('brew corepack', 'brew nodejs')
    with Path(brewfile).open('w') as f:
        f.write(content)
    helper.proc(f'"{cmd}" init -f "{brewfile}" -y --leaves')
    with Path(brewfile).open('r') as f:
        assert (
            f.read()
            == """
# tap repositories and their packages

tap homebrew/core
brew nodejs

tap homebrew/cask
cask paw
"""
        )

    # Test with not installed packages
    with Path(brewfile).open('r') as f:
        content = f.read()
    content = content.replace('brew nodejs', 'brew not_installed_formula')
    content = content.replace('cask paw', 'cask not_installed_cask')
    with Path(brewfile).open('w') as f:
        f.write(content)
    helper.proc(f'"{cmd}" init -f "{brewfile}" -y --leaves')
    with Path(brewfile).open('r') as f:
        assert (
            f.read()
            == """
# tap repositories and their packages

tap homebrew/core
brew node

tap homebrew/cask
cask rapidapi
"""
        )

    # Test with tap
    helper.proc('brew install rcmdnk/file/brew-file')
    helper.proc(f'"{cmd}" init -f "{brewfile}" -y --leaves')
    with Path(brewfile).open('r') as f:
        assert (
            f.read()
            == """
# tap repositories and their packages

tap homebrew/core
brew node

tap homebrew/cask
cask rapidapi

tap rcmdnk/file
brew brew-file
"""
        )

    helper.proc(f'"{cmd}" init -f "{brewfile}" -y --leaves --full-name')
    with Path(brewfile).open('r') as f:
        assert (
            f.read()
            == """
# tap repositories and their packages

tap homebrew/core
brew node

tap homebrew/cask
cask rapidapi

tap rcmdnk/file
brew rcmdnk/file/brew-file
"""
        )


@pytest.mark.parametrize(
    ('env', 'ls1', 'tap1', 'brewfile_content', 'ls2', 'tap2'),
    [
        pytest.param(
            {},
            [
                'brew-file',
                'brotli',
                'c-ares',
                'ca-certificates',
                'gettext',
                'git',
                'icu4c@77',
                'libnghttp2',
                'libunistring',
                'libuv',
                'node',
                'openssl@3',
                'pcre2',
                'rapidapi',
            ],
            ['rcmdnk/file'],
            """
# tap repositories and their packages

tap homebrew/core
brew brotli
brew c-ares
brew ca-certificates
brew gettext
brew git
brew icu4c@77
brew libnghttp2
brew libunistring
brew libuv
brew node
brew openssl@3
brew pcre2

tap homebrew/cask
cask rapidapi

tap rcmdnk/file
brew brew-file
""",
            ['gettext', 'git', 'libunistring', 'pcre2'],
            [],
            id='default',
        ),
        pytest.param(
            {'HOMEBREW_BREWFILE_ON_REQUEST': '1'},
            [
                'brew-file',
                'brotli',
                'c-ares',
                'ca-certificates',
                'gettext',
                'git',
                'icu4c@77',
                'libnghttp2',
                'libunistring',
                'libuv',
                'node',
                'openssl@3',
                'pcre2',
                'rapidapi',
            ],
            ['rcmdnk/file'],
            """
# tap repositories and their packages

tap homebrew/core
brew gettext
brew git
brew node

tap homebrew/cask
cask rapidapi

tap rcmdnk/file
brew brew-file
""",
            ['gettext', 'git', 'libunistring', 'pcre2'],
            [],
            id='on-request',
        ),
        pytest.param(
            {'HOMEBREW_BREWFILE_LEAVES': '1'},
            [
                'brew-file',
                'brotli',
                'c-ares',
                'ca-certificates',
                'gettext',
                'git',
                'icu4c@77',
                'libnghttp2',
                'libunistring',
                'libuv',
                'node',
                'openssl@3',
                'pcre2',
                'rapidapi',
            ],
            ['rcmdnk/file'],
            """
# tap repositories and their packages

tap homebrew/core
brew git
brew node

tap homebrew/cask
cask rapidapi

tap rcmdnk/file
brew brew-file
""",
            ['gettext', 'git', 'libunistring', 'pcre2'],
            [],
            id='leaves',
        ),
        pytest.param(
            {
                'HOMEBREW_BREWFILE_ON_REQUEST': '1',
                'HOMEBREW_BREWFILE_TOP_PACKAGES': 'gettext,pcre2',
            },
            [
                'brew-file',
                'brotli',
                'c-ares',
                'ca-certificates',
                'gettext',
                'git',
                'icu4c@77',
                'libnghttp2',
                'libunistring',
                'libuv',
                'node',
                'openssl@3',
                'pcre2',
                'rapidapi',
            ],
            ['rcmdnk/file'],
            """
# tap repositories and their packages

tap homebrew/core
brew gettext
brew git
brew node
brew pcre2

tap homebrew/cask
cask rapidapi

tap rcmdnk/file
brew brew-file
""",
            ['gettext', 'git', 'libunistring', 'pcre2'],
            [],
            id='top-packages',
        ),
    ],
)
def test_install_clean(
    cmd: str,
    brewfile: str,
    helper: BrewHelper,
    monkeypatch: pytest.MonkeyPatch,
    env: dict[str, Any],
    ls1: list[str],
    tap1: list[str],
    brewfile_content: str,
    ls2: list[str],
    tap2: list[str],
) -> None:
    for k, v in env.items():
        monkeypatch.setenv(k, v)

    with Path(brewfile).open('w') as f:
        f.write("""
tap homebrew/core
brew gettext
brew git
brew node
tap homebrew/cask
cask rapidapi
tapall rcmdnk/file
""")
    helper.proc(f'"{cmd}" install -f "{brewfile}"')
    _, lines = helper.proc('brew ls')
    assert lines == ls1
    _, lines = helper.proc('brew tap')
    assert lines == tap1

    helper.proc(f'"{cmd}" init -y -f "{brewfile}"')
    with Path(brewfile).open('r') as f:
        assert f.read() == brewfile_content

    with Path(brewfile).open('w') as f:
        f.write("""
tap homebrew/core
brew git
tap homebrew/cask
""")
        f.write('')
    helper.proc(f'"{cmd}" clean -f "{brewfile}"')
    _, lines = helper.proc('brew ls')
    assert lines == ls2
    _, lines = helper.proc('brew tap')
    assert lines == tap2


def test_vscode_cursor(
    cmd: str,
    brewfile: str,
    helper: BrewHelper,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv('HOMEBREW_BREWFILE_VSCODE', '1')
    monkeypatch.setenv('HOMEBREW_BREWFILE_CURSOR', '1')
    with Path(brewfile).open('w') as f:
        f.write("""
code ms-python.python
cursor ms-vscode.remote-explorer
""")
    helper.proc(f'"{cmd}" install -f "{brewfile}"')
    helper.proc(f'"{cmd}" init -f "{brewfile}" -y')
    with Path(brewfile).open('r') as f:
        assert (
            f.read()
            == """
# tap repositories and their packages

tap homebrew/core

tap homebrew/cask
cask cursor
cask visual-studio-code

# VSCode extensions
vscode ms-python.debugpy
vscode ms-python.python
vscode ms-python.vscode-pylance

# Cursor extensions
cursor ms-vscode.remote-explorer
"""
        )

    with Path(brewfile).open('w') as f:
        f.write("""
tap homebrew/core
tap homebrew/cask
cask visual-studio-code
vscode ms-python.vscode-pylance
""")
    helper.proc(f'"{cmd}" cleanup -f "{brewfile}"')
    helper.proc(f'"{cmd}" init -f "{brewfile}" -y')
    with Path(brewfile).open('r') as f:
        assert (
            f.read()
            == """
# tap repositories and their packages

tap homebrew/core

tap homebrew/cask
cask visual-studio-code

# VSCode extensions
vscode ms-python.vscode-pylance
"""
        )
