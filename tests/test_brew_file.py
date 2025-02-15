from __future__ import annotations

import io
import logging
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from .brew_file import BrewFile, BrewHelper, BrewInfo, __prog__, is_mac


@pytest.fixture
def bf() -> BrewFile:
    return BrewFile({})


def test_default_opt(bf: BrewFile) -> None:
    pass


def test_set_input(bf: BrewFile) -> None:
    bf.set_input('/path/to/file')
    assert bf.opt['input'] == Path('/path/to/file')
    assert bf.brewinfo.file == Path('/path/to/file')


def test_banner(bf: BrewFile, caplog: pytest.LogCaptureFixture) -> None:
    bf.banner('test banner')
    assert caplog.record_tuples == [
        (
            'tests.brew_file',
            logging.INFO,
            '\n###########\ntest banner\n###########\n',
        ),
    ]


def test_dryrun_banner(bf: BrewFile, caplog: pytest.LogCaptureFixture) -> None:
    bf.opt['dryrun'] = False
    with bf.DryrunBanner(bf):
        bf.log.info('test')
    assert caplog.record_tuples == [
        (
            'tests.brew_file',
            logging.INFO,
            'test',
        ),
    ]
    caplog.clear()
    bf.opt['dryrun'] = True
    with bf.DryrunBanner(bf):
        bf.log.info('test')
    assert caplog.record_tuples == [
        (
            'tests.brew_file',
            logging.INFO,
            '\n##################\n# This is dry run.\n##################\n',
        ),
        (
            'tests.brew_file',
            logging.INFO,
            'test',
        ),
        (
            'tests.brew_file',
            logging.INFO,
            '\n##################\n# This is dry run.\n##################\n',
        ),
    ]


def test_parse_env_opts(bf: BrewFile) -> None:
    with patch.dict('os.environ', {'TEST_OPT': '--opt2=3 --opt3 opt4=4'}):
        opts = bf.parse_env_opts('TEST_OPT', {'--opt1': '1', '--opt2': '2'})
        assert opts == {
            '--opt1': '1',
            '--opt2': '3',
            '--opt3': '',
            'opt4': '4',
        }


def test_set_verbose(bf: BrewFile) -> None:
    bf.set_verbose()
    assert bf.opt['verbose'] == 'info'
    assert bf.log.getEffectiveLevel() == logging.INFO
    with patch.dict('os.environ', {'HOMEBREW_BREWFILE_VERBOSE': 'error'}):
        bf.set_verbose()
    assert bf.opt['verbose'] == 'error'
    assert bf.log.getEffectiveLevel() == logging.ERROR
    bf.set_verbose('0')
    assert bf.opt['verbose'] == 'debug'
    assert bf.log.getEffectiveLevel() == logging.DEBUG


def test_set_args(bf: BrewFile) -> None:
    bf.opt['appstore'] = 1
    bf.opt['no_appstore'] = 1
    bf.set_args(a='1', verbose='1')
    assert bf.opt['a'] == '1'
    assert bf.opt['verbose'] == 'info'
    assert bf.opt['appstore'] == 1
    bf.opt['appstore'] = -1
    bf.opt['no_appstore'] = False
    bf.set_args()
    assert bf.opt['appstore'] == 1
    bf.opt['appstore'] = -1
    bf.opt['no_appstore'] = True
    bf.set_args()
    assert bf.opt['appstore'] == 0
    bf.opt['appstore'] = 1
    bf.opt['no_appstore'] = False
    bf.set_args()
    assert bf.opt['appstore'] == 1


@pytest.mark.parametrize(
    ('input_value', 'ret', 'out'),
    [
        ('y\n', True, 'Question? [y/n]: '),
        ('Y\n', True, 'Question? [y/n]: '),
        ('yes\n', True, 'Question? [y/n]: '),
        ('YES\n', True, 'Question? [y/n]: '),
        ('Yes\n', True, 'Question? [y/n]: '),
        ('n\n', False, 'Question? [y/n]: '),
        ('N\n', False, 'Question? [y/n]: '),
        ('no\n', False, 'Question? [y/n]: '),
        ('NO\n', False, 'Question? [y/n]: '),
        ('No\n', False, 'Question? [y/n]: '),
        (
            'a\nb\ny\n',
            True,
            'Question? [y/n]: Answer with yes (y) or no (n): Answer with yes (y) or no (n): ',
        ),
    ],
)
def test_ask_yn(
    bf: BrewFile,
    capsys: pytest.CaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
    input_value: str,
    ret: bool,
    out: str,
) -> None:
    monkeypatch.setattr('sys.stdin', io.StringIO(input_value))
    assert bf.ask_yn('Question?') == ret
    captured = capsys.readouterr()
    assert captured.out == out


def test_ask_yn_y(bf: BrewFile, caplog: pytest.LogCaptureFixture) -> None:
    bf.opt['yn'] = True
    assert bf.ask_yn('Question?')
    assert caplog.record_tuples == [
        ('tests.brew_file', logging.INFO, 'Question? [y/n]: y'),
    ]


@pytest.mark.parametrize(
    'full_name',
    [
        (False,),
        (True,),
    ],
)
def test_read_all(bf: BrewFile, tap: list[str], full_name: bool) -> None:
    parent = Path(__file__).parent / 'files'
    file = parent / 'BrewfileTest'
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
    assert bf.get_dict('brew_input_opt') == {
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


def test_read(bf: BrewFile, tmp_path: Path) -> None:
    helper = BrewHelper({})

    bf.brewinfo_ext = []
    file = Path(f'{Path(__file__).parent}/files/BrewfileMain')
    brewinfo = BrewInfo(helper=helper, file=file)
    ret = bf.read(brewinfo, True)
    assert ret.file == file

    bf.brewinfo_ext = []
    file = Path(f'{Path(__file__).parent}/files/BrewfileMain')
    brewinfo = BrewInfo(helper=helper, file=file)
    ret = bf.read(brewinfo, False)
    assert ret is None

    bf.brewinfo_ext = []
    file = Path(f'{Path(__file__).parent}/files/BrewfileTest')
    brewinfo = BrewInfo(helper=helper, file=file)
    ret = bf.read(brewinfo, True)
    file = Path(f'{Path(__file__).parent}/files/BrewfileMain')
    assert ret.file == file
    files = [
        Path(f'{Path(__file__).parent}/files/BrewfileMain'),
        Path(f'{Path(__file__).parent}/files/BrewfileExt'),
        Path(f'{Path(__file__).parent}/files/BrewfileExt2'),
        Path(f'{Path(__file__).parent}/files/BrewfileExt3'),
        Path(f'{Path(__file__).parent}/files/BrewfileNotExist'),
        Path(Path('~/BrewfileHomeForTestingNotExists').expanduser()),
    ]
    for i, f in zip(bf.brewinfo_ext, files):
        assert i.file == f

    # Absolute path check
    f1 = tmp_path / 'f1'
    f2 = tmp_path / 'f2'
    f3 = tmp_path / 'f3'
    with Path(f1).open('w') as f:
        f.write(f'main {f2}')
    with Path(f2).open('w') as f:
        f.write(f'main {f3}')

    bf.brewinfo_ext = []
    brewinfo = BrewInfo(helper=helper, file=f1)
    ret = bf.read(brewinfo, True)
    assert ret.file == Path(f3)


def test_list_to_main(bf: BrewFile) -> None:
    pass


def test_input_to_list(bf: BrewFile) -> None:
    pass


def test_write(bf: BrewFile) -> None:
    pass


def test_get(bf: BrewFile) -> None:
    pass


def test_remove_pack(bf: BrewFile) -> None:
    pass


def test_repo_name(bf: BrewFile) -> None:
    bf.opt['repo'] = 'git@github.com:abc/def.git'
    assert bf.repo_name() == 'def'
    bf.opt['repo'] = 'https://github.com/abc/def.git'
    assert bf.repo_name() == 'def'


def test_user_name(bf: BrewFile) -> None:
    bf.opt['repo'] = 'git@github.com:abc/def.git'
    assert bf.user_name() == 'abc'
    bf.opt['repo'] = 'https://github.com/abc/def.git'
    assert bf.user_name() == 'abc'


def test_input_dir(bf: BrewFile) -> None:
    pass


def test_input_file(bf: BrewFile) -> None:
    pass


def test_repo_file(bf: BrewFile) -> None:
    bf.set_input('/path/to/input')
    bf.user_name = lambda: 'user'
    bf.opt['repo'] = 'repo.git'
    assert bf.repo_file() == Path('/path/to/user_repo/input')


def test_init_repo(
    bf: BrewFile,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    bf.check_gitconfig = lambda: False
    file = tmp_path / 'Brewfile'
    bf.helper.proc('git init', cwd=tmp_path)
    bf.set_input(file)
    caplog.clear()
    bf.init_repo()
    assert caplog.record_tuples == [
        (
            'tests.brew_file',
            logging.INFO,
            'Initialize the repository with README.md/Brewfile.',
        ),
    ]
    assert (tmp_path / 'README.md').exists()
    assert file.exists()


def test_clone_repo(bf: BrewFile) -> None:
    pass


def test_check_github_repo(bf: BrewFile) -> None:
    pass


def test_check_local_repo(bf: BrewFile, tmp_path: Path) -> None:
    bf.opt['repo'] = f'file:///{tmp_path}/repo'
    bf.clone_repo = lambda: None
    bf.check_local_repo()
    assert (tmp_path / 'repo').exists()
    assert (tmp_path / 'repo' / '.git').exists()


def test_check_repo(bf: BrewFile) -> None:
    pass


def test_check_gitconfig(bf: BrewFile) -> None:
    pass


def test_repomgr(bf: BrewFile) -> None:
    pass


def test_brew_cmd(bf: BrewFile) -> None:
    pass


def test_add_path(bf: BrewFile) -> None:
    pass


def test_which_brew(bf: BrewFile) -> None:
    pass


def test_check_brew_cmd(bf: BrewFile) -> None:
    pass


def test_check_mas_cmd(bf: BrewFile) -> None:
    pass


def test_get_appstore_dict(bf: BrewFile) -> None:
    pass


def test_get_appstore_list(bf: BrewFile) -> None:
    pass


def test_get_cask_list(bf: BrewFile) -> None:
    pass


def test_get_list(bf: BrewFile) -> None:
    pass


def test_clean_list(bf: BrewFile) -> None:
    pass


def test_input_backup(bf: BrewFile) -> None:
    pass


def test_set_brewfile_repo(bf: BrewFile) -> None:
    pass


def test_set_brewfile_local(bf: BrewFile) -> None:
    pass


def test_initialize(bf: BrewFile) -> None:
    pass


def test_initialize_write(bf: BrewFile) -> None:
    pass


def test_check_input_file(bf: BrewFile) -> None:
    pass


def test_get_files(
    bf: BrewFile, tap: list[str], caplog: pytest.LogCaptureFixture
) -> None:
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


def test_edit_brewfile(bf: BrewFile) -> None:
    pass


def test_cat_brewfile(bf: BrewFile) -> None:
    pass


def test_clean_non_request(bf: BrewFile) -> None:
    bf.opt['dryrun'] = True
    bf.clean_non_request()


def test_cleanup(bf: BrewFile) -> None:
    pass


def test_install(bf: BrewFile) -> None:
    pass


@pytest.mark.parametrize(
    ('app', 'token'),
    [
        ('/App/ABC.app', 'abc'),
        ('/App/--A B  C--D+E@f-9.app', 'a-b-c-dpluseatf9'),
    ],
)
def test_generate_cask_token(bf: BrewFile, app: str, token: str) -> None:
    assert bf.generate_cask_token(app) == token


def test_find_app(bf: BrewFile) -> None:
    pass


def test_find_brew_app(bf: BrewFile) -> None:
    pass


def test_make_brew_app_cmd(bf: BrewFile) -> None:
    assert (
        bf.make_brew_app_cmd('abc', '/path/to/app')
        == 'brew abc # /path/to/app'
    )


def test_make_cask_app_cmd(bf: BrewFile) -> None:
    assert (
        bf.make_cask_app_cmd('abc', '/path/to/app')
        == 'cask abc # /path/to/app'
    )


def test_make_appstore_app_cmd(bf: BrewFile) -> None:
    assert (
        bf.make_appstore_app_cmd('abc', '/path/to/app')
        == 'appstore abc # /path/to/app'
    )


def test_check_cask(
    bf: BrewFile,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    os.chdir(tmp_path)
    if not is_mac():
        with pytest.raises(RuntimeError) as excinfo:
            bf.check_cask()
        assert str(excinfo.value) == 'Cask is not available on Linux!'
        return
    bf.check_cask()
    assert '# Starting to check applications for Cask...' in caplog.messages[0]
    assert '# Summary' in ''.join(caplog.messages)
    assert Path('Caskfile').exists()
    with Path('Caskfile').open() as f:
        lines = f.readlines()
    assert lines[0] == '# Cask applications\n'


@pytest.fixture
def execute_fixture(monkeypatch: pytest.MonkeyPatch) -> BrewFile:
    for func in [
        'check_brew_cmd',
        'check_cask',
        'set_brewfile_repo',
        'set_brewfile_local',
        'check_repo',
        'repomgr',
        'brew_cmd',
        'initialize',
        'check_input_file',
        'edit_brewfile',
        'cat_brewfile',
        'get_files',
        'clean_non_request',
        'cleanup',
        'install',
    ]:

        def set_func(func: str) -> None:
            # make local variable, needed to keep in print view
            name = func
            monkeypatch.setattr(
                BrewFile,
                func,
                lambda self, *args, **kw: print(name, args, kw),  # noqa: T201
            )

        set_func(func)
    monkeypatch.setattr(
        BrewFile,
        'check_brew_cmd',
        lambda self: None,
    )
    monkeypatch.setattr(BrewHelper, 'brew_val', lambda self, x: x)
    monkeypatch.setattr(
        BrewHelper,
        'proc',
        lambda self, *args, **kw: print('proc', args, kw),  # noqa: T201
    )
    return BrewFile({})


@pytest.mark.parametrize(
    ('command', 'out'),
    [
        ('casklist', 'check_cask () {}\n'),
        ('set_repo', 'set_brewfile_repo () {}\n'),
        ('set_local', 'set_brewfile_local () {}\n'),
        ('pull', "check_repo () {}\nrepomgr ('pull',) {}\n"),
        ('push', "check_repo () {}\nrepomgr ('push',) {}\n"),
        ('brew', 'check_repo () {}\nbrew_cmd () {}\n'),
        ('init', 'check_repo () {}\ninitialize () {}\n'),
        ('dump', 'check_repo () {}\ninitialize () {}\n'),
        (
            'edit',
            'check_repo () {}\nedit_brewfile () {}\n',
        ),
        (
            'cat',
            'check_repo () {}\ncat_brewfile () {}\n',
        ),
        (
            'get_files',
            "check_repo () {}\nget_files () {'is_print': True, 'all_files': False}\n",
        ),
        (
            'clean_non_request',
            'check_repo () {}\ncheck_input_file () {}\nclean_non_request () {}\n',
        ),
        (
            'clean',
            'check_repo () {}\ncheck_input_file () {}\ncleanup () {}\n',
        ),
    ],
)
def test_execute(
    execute_fixture: BrewFile,
    capsys: pytest.CaptureFixture,
    command: str,
    out: str,
) -> None:
    bf = execute_fixture
    bf.opt['command'] = command
    bf.execute()
    captured = capsys.readouterr()
    assert captured.out == out


def test_execute_update(
    execute_fixture: BrewFile,
    capsys: pytest.CaptureFixture,
) -> None:
    bf = execute_fixture
    bf.opt['command'] = 'update'
    bf.execute()
    captured = capsys.readouterr()
    if is_mac():
        assert (
            captured.out
            == "check_repo () {}\ncheck_input_file () {}\nproc ('brew update',) {'dryrun': False}\nproc ('brew upgrade --formula ',) {'dryrun': False}\nproc ('brew upgrade --cask',) {'dryrun': False}\ninstall () {}\ncleanup () {'delete_cache': False}\ninitialize () {'check': False, 'debug_out': True}\n"
        )
    else:
        assert (
            captured.out
            == "check_repo () {}\ncheck_input_file () {}\nproc ('brew update',) {'dryrun': False}\nproc ('brew upgrade --formula ',) {'dryrun': False}\ninstall () {}\ncleanup () {'delete_cache': False}\ninitialize () {'check': False, 'debug_out': True}\n"
        )


def test_execute_err(execute_fixture: BrewFile) -> None:
    bf = execute_fixture
    bf.opt['command'] = 'wrong_command'
    with pytest.raises(RuntimeError) as excinfo:
        bf.execute()
    assert (
        str(excinfo.value)
        == f'Wrong command: wrong_command\nExecute `{__prog__} help` for more information.'
    )
