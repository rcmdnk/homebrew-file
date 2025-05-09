# ruff: noqa: S605
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import pytest

from .brew_file import BrewFile, BrewHelper, BrewInfo, is_mac

# DO NOT run this test in your local environment.
# Tests using the system Homebrew environment.
# They remove all packages at the beginning.

pytestmark = pytest.mark.destructive


if not is_mac():
    pytest.skip('skipping macOS tests', allow_module_level=True)


@pytest.fixture(autouse=True)
def clean(request: pytest.FixtureRequest) -> None:
    if request.config.destructive_clean:
        clean_script = Path(__file__).parent / 'scripts' / 'clean_homebrew.sh'
        os.system(f'"{clean_script}"')


@pytest.fixture
def brewfile(tmp_path: Path) -> str:
    file = tmp_path / 'Brewfile'
    file.touch()
    return str(file)


@pytest.fixture
def backup(tmp_path: Path) -> str:
    return tmp_path / 'Brewfile.bak'


@pytest.fixture
def tmp_log(tmp_path: Path) -> str:
    return tmp_path / 'log'


# For BrewHelper


@pytest.mark.destructive_get_tap_packs
def test_get_tap_packs(helper: BrewHelper) -> None:
    helper.proc('brew tap rcmdnk/rcmdnkpac')
    helper.proc('brew tap rcmdnk/rcmdnkcask')

    packs = helper.get_tap_packs('rcmdnk/rcmdnkpac')
    assert 'chatgpt-prompt-wrapper' in packs['formulae']
    if is_mac():
        packs = helper.get_tap_packs('rcmdnk/rcmdnkcask')
        assert 'vem' in packs['casks']

    # Test with alias=True
    helper.proc('brew install node')
    packs_wo_alias = helper.get_tap_packs('homebrew/core')
    packs_with_alias = helper.get_tap_packs('homebrew/core', alias=True)
    # aliases are added only when the formula is installed
    # node and its dependencies have some (oldnames, aliases):
    # - node: (1, 4)
    # - icu4c@77: (0, 1)
    # - openssl@3: (0, 2)
    assert (
        len(packs_with_alias['formulae'])
        == len(packs_wo_alias['formulae']) + 8
    )


@pytest.mark.destructive_get_leaves
def test_get_leaves(helper: BrewHelper) -> None:
    helper.proc('brew install node')
    helper.proc('brew install brotli')
    helper.proc('brew install ccat')
    helper.proc('brew tab --no-installed-on-request ccat')
    leaves = helper.get_leaves()
    assert leaves == ['ccat', 'node']
    leaves = helper.get_leaves(on_request=True)
    assert leaves == ['node']


@pytest.mark.destructive_full_name
def test_get_full_name(helper: BrewHelper) -> None:
    helper.proc('brew install git')
    helper.proc('brew install rcmdnk/file/brew-file')

    # Test core formula
    assert helper.get_full_name('git') == 'git'

    # Test tap formula
    assert helper.get_full_name('brew-file') == 'rcmdnk/file/brew-file'


# For BrewInfo


# Ignore DeprecationWarning to allow \$
@pytest.mark.filterwarnings('ignore::DeprecationWarning')
@pytest.mark.destructive_others
def test_write(
    helper: BrewHelper, brew_info: BrewInfo, tmp_path: Path
) -> None:
    helper.proc('brew tap rcmdnk/rcmdnkpac')
    helper.proc('brew tap rcmdnk/rcmdnkcask')
    tmp_file = tmp_path / 'f'
    default_file = brew_info.file
    brew_info.helper.opt['caskonly'] = False
    brew_info.helper.opt['appstore'] = -1
    brew_info.helper.opt['verbose'] = 1
    brew_info.helper.opt['form'] = None
    brew_info.read()
    brew_info.input_to_list()
    brew_info.file = tmp_file
    brew_info.write()
    with Path(default_file).open() as f1:
        # Remove first and last ignore sections
        default_txt = [
            x
            for x in f1
            if x
            not in [
                '#BREWFILE_IGNORE\n',
                '#BREWFILE_ENDIGNORE\n',
                'brew abc\n',
                'brew xyz\n',
            ]
        ]
        default_txt = default_txt[1:-1]

        default_txt = ''.join(default_txt)
    with Path(tmp_file).open() as f2:
        tmp_txt = f2.read()
    assert tmp_txt == default_txt
    brew_info.helper.opt['form'] = 'bundle'
    brew_info.write()
    if is_mac():
        cask_tap1 = "\ntap 'homebrew/cask'\n\ntap 'rcmdnk/rcmdnkcask'\n"
        cask_tap2 = '\nbrew tap homebrew/cask\n\nbrew tap rcmdnk/rcmdnkcask\n'
        appstore1 = "\n# App Store applications\nmas '', id: Keynote\n"
        appstore2 = '\n# App Store applications\nmas install Keynote\n'
    else:
        cask_tap1 = ''
        cask_tap2 = ''
        appstore1 = ''
        appstore2 = ''

    with Path(tmp_file).open() as f2:
        assert (
            f2.read()
            == f"""# Before commands
#before echo before

# tap repositories and their packages

tap 'homebrew/core'
{cask_tap1}{appstore1}
# Main file
#main 'BrewfileMain'

# Additional files
#file 'BrewfileExt'
#file 'BrewfileExt2'
#file 'BrewfileNotExist'
#file '~/BrewfileHomeForTestingNotExists'

# Other commands
#echo other commands

# After commands
#after echo after
"""
        )

        brew_info.helper.opt['form'] = 'cmd'
        brew_info.write()
        with Path(tmp_file).open() as f3:
            assert (
                f3.read()
                == f"""#!/usr/bin/env bash

#BREWFILE_IGNORE
if ! which brew >& /dev/null;then
  brew_installed=0
  echo Homebrew is not installed!
  echo Install now...
  echo /bin/bash -c \\\"\\$\\(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh\\)\\\"
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"
  echo
fi
#BREWFILE_ENDIGNORE

# Before commands
echo before

# tap repositories and their packages

brew tap homebrew/core
{cask_tap2}{appstore2}
# Main file
#main BrewfileMain

# Additional files
#file BrewfileExt
#file BrewfileExt2
#file BrewfileNotExist
#file ~/BrewfileHomeForTestingNotExists

# Other commands
echo other commands

# After commands
echo after
"""
            )


# For BrewFile


@pytest.mark.destructive_others
@pytest.mark.parametrize(
    'full_name',
    [
        (False,),
        (True,),
    ],
)
def test_read_all(full_name: bool) -> None:
    bf = BrewFile({})
    bf.helper.proc('brew tap rcmdnk/rcmdnkpac')
    bf.helper.proc('brew tap rcmdnk/rcmdnkcask')
    parent = Path(__file__).parent / 'files'
    file = parent / ('BrewfileTest' if is_mac() else 'BrewfileTestLinux')
    bf.opt['full_name'] = full_name
    tap = 'rcmdnk/rcmdnkpac/' if full_name else ''
    bf.set_input(file)
    bf.read_all()
    assert bf.brewinfo_main.file == parent / 'BrewfileMain'
    assert [x.file for x in bf.brewinfo_ext] == [
        parent / x
        for x in [
            'BrewfileTest',
            'BrewfileExt',
            'BrewfileExt2',
            'BrewfileExt3',
            'BrewfileNotExist',
        ]
    ] + [Path(os.environ['HOME']) / 'BrewfileHomeForTestingNotExists']
    assert bf.get_list('brew_input') == {
        'cmake',
        'python@3.10',
        'vim',
        f'{tap}chatgpt-prompt-wrapper',
        f'{tap}cocoro',
        f'{tap}ec2',
        f'{tap}escape_sequence',
        f'{tap}evernote_mail',
        f'{tap}gcp-tools',
        f'{tap}gmail_filter_manager',
        f'{tap}git-gpt-commit',
        f'{tap}gtask',
        f'{tap}inputsource',
        f'{tap}multi_clipboard',
        f'{tap}open_newtab',
        f'{tap}parse-plist',
        f'{tap}po',
        f'{tap}rcmdnk-sshrc',
        f'{tap}rcmdnk-trash',
        f'{tap}screenutf8',
        f'{tap}sd_cl',
        f'{tap}sentaku',
        f'{tap}shell-explorer',
        f'{tap}shell-logger',
        f'{tap}smenu',
        f'{tap}stow_reset',
    }
    assert bf.get_dict('brew_opt_input') == {
        'cmake': '',
        'python@3.10': '',
        'vim': ' --HEAD',
        f'{tap}chatgpt-prompt-wrapper': '',
        f'{tap}cocoro': '',
        f'{tap}ec2': '',
        f'{tap}escape_sequence': '',
        f'{tap}evernote_mail': '',
        f'{tap}gcp-tools': '',
        f'{tap}gmail_filter_manager': '',
        f'{tap}git-gpt-commit': '',
        f'{tap}gtask': '',
        f'{tap}inputsource': '',
        f'{tap}multi_clipboard': '',
        f'{tap}open_newtab': '',
        f'{tap}parse-plist': '',
        f'{tap}po': '',
        f'{tap}rcmdnk-sshrc': '',
        f'{tap}rcmdnk-trash': '',
        f'{tap}screenutf8': '',
        f'{tap}sd_cl': '',
        f'{tap}sentaku': '',
        f'{tap}shell-explorer': '',
        f'{tap}shell-logger': '',
        f'{tap}smenu': '',
        f'{tap}stow_reset': '',
    }
    assert bf.get_list('tap_input') == {
        'homebrew/cask',
        'homebrew/core',
        'rcmdnk/rcmdnkcask',
        'rcmdnk/rcmdnkpac',
    }
    if is_mac():
        assert bf.get_list('cask_input') == {'iterm2', 'font-migu1m'}
        assert bf.get_list('appstore_input') == {'Keynote'}
    assert bf.get_list('main_input') == {'BrewfileMain'}
    assert bf.get_list('file_input') == {
        'BrewfileMain',
        'BrewfileExt',
        'BrewfileExt2',
        'BrewfileNotExist',
        '~/BrewfileHomeForTestingNotExists',
        'BrewfileExt3',
    }
    assert bf.get_list('before_input') == {'echo before', 'echo EXT before'}
    assert bf.get_list('after_input') == {'echo after', 'echo EXT after'}
    assert bf.get_list('cmd_input') == {
        'echo BrewfileMain',
        'echo other commands',
    }


@pytest.mark.destructive_others
def test_get_files(caplog: pytest.LogCaptureFixture) -> None:
    bf = BrewFile({})
    bf.helper.proc('brew tap rcmdnk/rcmdnkpac')
    bf.helper.proc('brew tap rcmdnk/rcmdnkcask')
    parent = Path(__file__).parent / 'files'
    file = parent / 'BrewfileTest'
    bf.set_input(file)
    files = [
        parent / x
        for x in [
            'BrewfileMain',
            'BrewfileTest',
            'BrewfileExt',
            'BrewfileExt2',
        ]
    ]
    caplog.clear()
    assert bf.get_files() == files
    # record could include 'Error: Another active Homebrew update process is already in progress.' by another test
    assert (
        'tests.brew_file',
        20,
        '$ brew tap rcmdnk/rcmdnkpac',
    ) in caplog.record_tuples

    bf.set_input(file)
    bf.opt['read'] = False
    files = [
        parent / x
        for x in [
            'BrewfileMain',
            'BrewfileTest',
            'BrewfileExt',
            'BrewfileExt2',
            'BrewfileExt3',
            'BrewfileNotExist',
            Path(os.environ['HOME']) / 'BrewfileHomeForTestingNotExists',
        ]
    ]
    caplog.clear()
    assert bf.get_files(is_print=True, all_files=True) == files
    assert caplog.record_tuples == [
        ('tests.brew_file', 20, '$ brew tap rcmdnk/rcmdnkpac'),
        (
            'tests.brew_file',
            logging.INFO,
            '\n'.join([str(x) for x in files]),
        ),
    ]


# Other E2E tests with brew-file command


@pytest.mark.destructive_init
def test_init(
    bf_cmd: str,
    brewfile: str,
    helper: BrewHelper,
    backup: Path,
    tmp_path: Path,
) -> None:
    # Test with no packages
    helper.proc(f'"{bf_cmd}" init -f "{brewfile}" -y')
    cask_part = (
        """

tap homebrew/cask"""
        if is_mac()
        else ''
    )

    with Path(brewfile).open('r') as f:
        assert (
            f.read()
            == f"""
# tap repositories and their packages

tap homebrew/core{cask_part}
"""
        )

    # Test with some packages, with backup
    helper.proc('brew install brotli')
    helper.proc('brew install node')
    helper.proc('brew install rapidapi')
    helper.proc(f'"{bf_cmd}" init -f "{brewfile}" -y -b {backup}')
    cask_part = (
        """

tap homebrew/cask
cask rapidapi"""
        if is_mac()
        else ''
    )
    with Path(brewfile).open('r') as f:
        assert (
            f.read()
            == f"""
# tap repositories and their packages

tap homebrew/core
brew brotli
brew c-ares
brew ca-certificates
brew icu4c@77
brew libnghttp2
brew libuv
brew node
brew openssl@3{cask_part}
"""
        )
    cask_part = (
        """

tap homebrew/cask"""
        if is_mac()
        else ''
    )
    with Path(f'{backup}').open('r') as f:
        assert (
            f.read()
            == f"""
# tap repositories and their packages

tap homebrew/core{cask_part}
"""
        )

    # test with --caskonly
    if is_mac():
        helper.proc(f'"{bf_cmd}" init -f "{brewfile}" -y --caskonly')
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
    helper.proc(f'"{bf_cmd}" init -f "{brewfile}" -y --on-request')
    cask_part = (
        """

tap homebrew/cask
cask rapidapi"""
        if is_mac()
        else ''
    )
    with Path(brewfile).open('r') as f:
        assert (
            f.read()
            == f"""
# tap repositories and their packages

tap homebrew/core
brew brotli
brew node{cask_part}
"""
        )

    # Test with --top-packages
    helper.proc(
        f'"{bf_cmd}" init -f "{brewfile}" -y --on-request --top-packages c-ares,libuv'
    )
    with Path(brewfile).open('r') as f:
        assert (
            f.read()
            == f"""
# tap repositories and their packages

tap homebrew/core
brew brotli
brew c-ares
brew libuv
brew node{cask_part}
"""
        )

    # Test with --leaves
    helper.proc(f'"{bf_cmd}" init -f "{brewfile}" -y --leaves')
    with Path(brewfile).open('r') as f:
        assert (
            f.read()
            == f"""
# tap repositories and their packages

tap homebrew/core
brew node{cask_part}
"""
        )

    # Test with format
    helper.proc(f'"{bf_cmd}" init -f "{brewfile}" -y --leaves -F bundle')
    cask_part = (
        """

tap 'homebrew/cask'
cask 'rapidapi'"""
        if is_mac()
        else ''
    )
    with Path(brewfile).open('r') as f:
        assert (
            f.read()
            == f"""
# tap repositories and their packages

tap 'homebrew/core'
brew 'node'{cask_part}
"""
        )

    helper.proc(f'"{bf_cmd}" init -f "{brewfile}" -y --leaves -F cmd')
    cask_part = (
        """

brew tap homebrew/cask
brew install rapidapi"""
        if is_mac()
        else ''
    )
    with Path(brewfile).open('r') as f:
        assert (
            f.read()
            == f"""#!/usr/bin/env bash

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
brew install node{cask_part}
"""
        )

    helper.proc(f'"{bf_cmd}" init -f "{brewfile}" -y --leaves -F file')
    cask_part = (
        """

tap homebrew/cask
cask rapidapi"""
        if is_mac()
        else ''
    )
    with Path(brewfile).open('r') as f:
        assert (
            f.read()
            == f"""
# tap repositories and their packages

tap homebrew/core
brew node{cask_part}
"""
        )

    # Test with oldnames and old_tokens
    with Path(brewfile).open('r') as f:
        content = f.read()
    content = content.replace('brew node', 'brew corepack')
    content = content.replace('cask rapidapi', 'cask paw')
    with Path(brewfile).open('w') as f:
        f.write(content)
    helper.proc(f'"{bf_cmd}" init -f "{brewfile}" -y --leaves')
    cask_part = (
        """

tap homebrew/cask
cask paw"""
        if is_mac()
        else ''
    )
    with Path(brewfile).open('r') as f:
        assert (
            f.read()
            == f"""
# tap repositories and their packages

tap homebrew/core
brew corepack{cask_part}
"""
        )

    # Test with aliases
    with Path(brewfile).open('r') as f:
        content = f.read()
    content = content.replace('brew corepack', 'brew nodejs')
    with Path(brewfile).open('w') as f:
        f.write(content)
    helper.proc(f'"{bf_cmd}" init -f "{brewfile}" -y --leaves')
    with Path(brewfile).open('r') as f:
        assert (
            f.read()
            == f"""
# tap repositories and their packages

tap homebrew/core
brew nodejs{cask_part}
"""
        )

    # Test with not installed packages
    with Path(brewfile).open('r') as f:
        content = f.read()
    content = content.replace('brew nodejs', 'brew not_installed_formula')
    content = content.replace('cask paw', 'cask not_installed_cask')
    with Path(brewfile).open('w') as f:
        f.write(content)
    helper.proc(f'"{bf_cmd}" init -f "{brewfile}" -y --leaves')
    cask_part = (
        """

tap homebrew/cask
cask rapidapi"""
        if is_mac()
        else ''
    )
    with Path(brewfile).open('r') as f:
        assert (
            f.read()
            == f"""
# tap repositories and their packages

tap homebrew/core
brew node{cask_part}
"""
        )

    # Test with tap
    helper.proc('brew install rcmdnk/file/brew-file')
    helper.proc(f'"{bf_cmd}" init -f "{brewfile}" -y --leaves')
    with Path(brewfile).open('r') as f:
        assert (
            f.read()
            == f"""
# tap repositories and their packages

tap homebrew/core
brew node{cask_part}

tap rcmdnk/file
brew brew-file
"""
        )

    helper.proc(f'"{bf_cmd}" init -f "{brewfile}" -y --leaves --full-name')
    with Path(brewfile).open('r') as f:
        assert (
            f.read()
            == f"""
# tap repositories and their packages

tap homebrew/core
brew node{cask_part}

tap rcmdnk/file
brew rcmdnk/file/brew-file
"""
        )


@pytest.mark.parametrize(
    (
        'env',
        'ls1_formulae',
        'ls1_casks',
        'tap1',
        'brewfile_content',
        'cask_part',
        'ls2_formulae',
        'ls2_casks',
        'tap2',
    ),
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
            ],
            [
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
brew pcre2{}

tap rcmdnk/file
brew brew-file
""",
            """

tap homebrew/cask
cask rapidapi""",
            ['gettext', 'git', 'libunistring', 'pcre2'],
            [],
            [],
            id='default',
            marks=pytest.mark.destructive_install_clean_default,
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
            ],
            [
                'rapidapi',
            ],
            ['rcmdnk/file'],
            """
# tap repositories and their packages

tap homebrew/core
brew gettext
brew git
brew node{}

tap rcmdnk/file
brew brew-file
""",
            """

tap homebrew/cask
cask rapidapi""",
            ['gettext', 'git', 'libunistring', 'pcre2'],
            [],
            [],
            id='on-request',
            marks=pytest.mark.destructive_install_clean_on_request,
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
            ],
            [
                'rapidapi',
            ],
            ['rcmdnk/file'],
            """
# tap repositories and their packages

tap homebrew/core
brew git
brew node{}

tap rcmdnk/file
brew brew-file
""",
            """

tap homebrew/cask
cask rapidapi""",
            ['gettext', 'git', 'libunistring', 'pcre2'],
            [],
            [],
            id='leaves',
            marks=pytest.mark.destructive_install_clean_leaves,
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
            ],
            [
                'rapidapi',
            ],
            ['rcmdnk/file'],
            """
# tap repositories and their packages

tap homebrew/core
brew gettext
brew git
brew node
brew pcre2{}

tap rcmdnk/file
brew brew-file
""",
            """

tap homebrew/cask
cask rapidapi""",
            ['gettext', 'git', 'libunistring', 'pcre2'],
            [],
            [],
            id='top-packages',
            marks=pytest.mark.destructive_install_clean_top_packages,
        ),
    ],
)
def test_install_clean(
    bf_cmd: str,
    brewfile: str,
    helper: BrewHelper,
    monkeypatch: pytest.MonkeyPatch,
    env: dict[str, Any],
    ls1_formulae: list[str],
    ls1_casks: list[str],
    tap1: list[str],
    brewfile_content: str,
    cask_part: str,
    ls2_formulae: list[str],
    ls2_casks: list[str],
    tap2: list[str],
) -> None:
    for k, v in env.items():
        monkeypatch.setenv(k, v)

    with Path(brewfile).open('w') as f:
        f.write("""
brew gettext
brew git
brew node
tapall rcmdnk/file
""")
        if is_mac():
            f.write("""
cask rapidapi
""")

    helper.proc(f'"{bf_cmd}" install -f "{brewfile}"')
    _, lines = helper.proc('brew ls')
    assert lines == ls1_formulae + ls1_casks
    _, lines = helper.proc('brew tap')
    assert lines == tap1

    helper.proc(f'"{bf_cmd}" init -y -f "{brewfile}"')
    with Path(brewfile).open('r') as f:
        assert f.read() == brewfile_content.format(
            cask_part if is_mac() else ''
        )

    with Path(brewfile).open('w') as f:
        f.write("""
brew git
""")
    helper.proc(f'"{bf_cmd}" clean -f "{brewfile}"')
    _, lines = helper.proc('brew ls')
    assert lines == ls2_formulae + ls2_casks
    _, lines = helper.proc('brew tap')
    assert lines == tap2


@pytest.mark.destructive_others
def test_clean_non_request(
    bf_cmd: str,
    brewfile: str,
    helper: BrewHelper,
) -> None:
    helper.proc('brew install brotli')
    helper.proc(f'"{bf_cmd}" clean_non_request -f "{brewfile}"')
    _, lines = helper.proc('brew ls')
    assert lines == ['brotli']
    helper.proc('brew tab --no-installed-on-request brotli')
    helper.proc(f'"{bf_cmd}" clean_non_request -f "{brewfile}"')
    _, lines = helper.proc('brew ls')
    assert lines == []


# Test only cursor, as uninstalling VSCode requires root permission
@pytest.mark.destructive_cursor
def test_cursor(
    bf_cmd: str,
    brewfile: str,
    helper: BrewHelper,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if not is_mac():
        pytest.skip('only for mac')
    monkeypatch.setenv('HOMEBREW_BREWFILE_CURSOR', '1')
    with Path(brewfile).open('w') as f:
        f.write("""
cursor ms-python.python
cursor ms-vscode.remote-explorer
""")
    helper.proc(f'"{bf_cmd}" install -f "{brewfile}"')
    helper.proc(f'"{bf_cmd}" init -f "{brewfile}" -y')
    with Path(brewfile).open('r') as f:
        assert (
            f.read()
            == """
# tap repositories and their packages

tap homebrew/core

tap homebrew/cask
cask cursor

# Cursor extensions
cursor ms-python.debugpy
cursor ms-python.python
cursor ms-python.vscode-pylance
cursor ms-vscode.remote-explorer
"""
        )

    with Path(brewfile).open('w') as f:
        f.write("""
tap homebrew/core
tap homebrew/cask
cask cursor
cursor ms-vscode.remote-explorer
""")
    helper.proc(f'"{bf_cmd}" clean -f "{brewfile}"')
    helper.proc(f'"{bf_cmd}" init -f "{brewfile}" -y')
    with Path(brewfile).open('r') as f:
        assert (
            f.read()
            == """
# tap repositories and their packages

tap homebrew/core

tap homebrew/cask
cask cursor

# Cursor extensions
cursor ms-vscode.remote-explorer
"""
        )


@pytest.mark.destructive_update
def test_update(
    bf_cmd: str, brewfile: str, helper: BrewHelper, tmp_path: Path
) -> None:
    repo = tmp_path / 'test/repo'
    local_repo = tmp_path / 'test_repo'
    helper.proc('brew install git')
    helper.proc(f'"{bf_cmd}" set_repo --repo file://{repo} -f "{brewfile}" -y')
    helper.proc(f'"{bf_cmd}" init -f "{brewfile}" -y')
    helper.proc(f'"{bf_cmd}" update -f "{brewfile}"')

    cask_part = """

tap homebrew/cask"""

    with Path(local_repo / 'Brewfile').open('r') as f:
        assert (
            f.read()
            == f"""
# tap repositories and their packages

tap homebrew/core
brew gettext
brew git
brew libunistring
brew pcre2{cask_part}
"""
        )
    with Path(repo / 'Brewfile').open('r') as f:
        assert (
            f.read()
            == f"""
# tap repositories and their packages

tap homebrew/core
brew gettext
brew git
brew libunistring
brew pcre2{cask_part}
"""
        )


@pytest.mark.destructive_dry_run
def test_dry_run(
    bf_cmd: str,
    brewfile: str,
    helper: BrewHelper,
) -> None:
    # Create Brewfile with a package
    with Path(brewfile).open('w') as f:
        f.write('tap homebrew/core\nbrew git\n')

    # Test install with dry run
    helper.proc(f'"{bf_cmd}" install -f "{brewfile}" -d')
    _, lines = helper.proc('brew ls')
    assert 'git' not in lines

    # Test install w/o dry run
    helper.proc(f'"{bf_cmd}" install -f "{brewfile}"')
    _, lines = helper.proc('brew ls')
    assert 'git' in lines

    # Remove git from Brewfile
    with Path(brewfile).open('w') as f:
        f.write('tap homebrew/core')

    # Test clean with dry run
    helper.proc(f'"{bf_cmd}" clean -f "{brewfile}" -d')
    _, lines = helper.proc('brew ls')
    assert 'git' in lines

    # Test clean w/o dry run
    helper.proc(f'"{bf_cmd}" clean -f "{brewfile}"')
    _, lines = helper.proc('brew ls')
    assert 'git' not in lines


@pytest.mark.destructive_brew_command
def test_brew_command(
    bf_cmd: str,
    brewfile: str,
    helper: BrewHelper,
) -> None:
    # Test direct brew command
    helper.proc(f'"{bf_cmd}" brew install git')
    _, lines = helper.proc('brew ls')
    assert 'git' in lines

    # Test brew command with noinit
    helper.proc(f'"{bf_cmd}" brew noinit install node')
    _, lines = helper.proc('brew ls')
    assert 'node' in lines


@pytest.mark.destructive_format_options
def test_format_options(
    bf_cmd: str,
    brewfile: str,
    helper: BrewHelper,
) -> None:
    # Test different format options
    helper.proc('brew install git')
    formats = ['file', 'bundle', 'cmd']
    for fmt in formats:
        helper.proc(f'"{bf_cmd}" init -f "{brewfile}" -y --no-repo -F {fmt}')
        assert Path(brewfile).exists()
        with Path(brewfile).open() as f:
            content = f.read()
        if fmt == 'file':
            assert 'brew git' in content
        elif fmt == 'bundle':
            assert "brew 'git'" in content
        elif fmt == 'cmd':
            assert 'brew install git' in content


@pytest.mark.destructive_others
def test_cask_args(
    bf_cmd: str,
    brewfile: str,
    helper: BrewHelper,
    tmp_path: Path,
) -> None:
    if not is_mac():
        pytest.skip('Cask args test is only for macOS')
    # Test cask_args in different formats
    formats = ['file', 'bundle']
    app_path = tmp_path / 'Applications'
    for fmt in formats:
        with Path(brewfile).open('w') as f:
            if fmt == 'bundle':
                f.write(f"cask_args appdir: '{app_path}'\ncask 'rapidapi'\n")
            else:
                f.write(f"cask_args --appdir='{app_path}'\ncask rapidapi\n")
        helper.proc(f'"{bf_cmd}" install -f "{brewfile}"')
        assert Path(f'{app_path}/RapidAPI.app').expanduser().exists()
        helper.proc('brew rm rapidapi')


@pytest.mark.destructive_main_file_inheritance
def test_main_file_inheritance(
    bf_cmd: str,
    brewfile: str,
    helper: BrewHelper,
    tmp_path: Path,
) -> None:
    # Create main and host-specific Brewfiles
    main_file = tmp_path / 'main.Brewfile'
    host_file = tmp_path / f'Brewfile.{os.uname().nodename}'

    # Setup main Brewfile
    with Path(brewfile).open('w') as f:
        f.write(f"""
tap homebrew/core
brew git
main {main_file}
file {host_file}
""")

    # Setup host-specific Brewfile
    with Path(host_file).open('w') as f:
        f.write('brew node')

    # Install packages and verify
    helper.proc(f'"{bf_cmd}" install -f "{brewfile}"')
    _, lines = helper.proc('brew ls')
    assert 'git' in lines
    assert 'node' in lines

    # Test that new packages go to main file
    helper.proc('brew install brotli')
    helper.proc(f'"{bf_cmd}" init -f "{brewfile}" -y')

    with Path(main_file).open() as f:
        content = f.read()
        assert 'brew brotli' in content
