from __future__ import annotations

import io
import logging
import os
from pathlib import Path

import pytest

from .brew_file import (
    BrewFile,
    BrewHelper,
    BrewInfo,
    CmdError,
    __prog__,
    is_mac,
)


@pytest.fixture
def bf() -> BrewFile:
    return BrewFile({})


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


def test_parse_env_opts(bf: BrewFile, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('TEST_OPT', '--opt2=3 --opt3 opt4=4')
    opts = bf.parse_env_opts('TEST_OPT', {'--opt1': '1', '--opt2': '2'})
    assert opts == {
        '--opt1': '1',
        '--opt2': '3',
        '--opt3': '',
        'opt4': '4',
    }


def test_set_verbose(bf: BrewFile, monkeypatch: pytest.MonkeyPatch) -> None:
    bf.set_verbose()
    assert bf.opt['verbose'] == 'info'
    assert bf.log.getEffectiveLevel() == logging.INFO
    monkeypatch.setenv('HOMEBREW_BREWFILE_VERBOSE', 'error')
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


def test_check_local_repo(bf: BrewFile, tmp_path: Path) -> None:
    bf.opt['repo'] = f'file:///{tmp_path}/repo'
    bf.clone_repo = lambda: None
    bf.check_local_repo()
    assert (tmp_path / 'repo').exists()
    assert (tmp_path / 'repo' / '.git').exists()


def test_set_brewfile_repo(tmp_path: Path) -> None:
    file = tmp_path / 'Brewfile'
    repo = tmp_path / 'test/repo'
    local_repo = tmp_path / 'test_repo'
    bf = BrewFile(
        opt={'input': str(file), 'repo': f'file://{repo}', 'yn': True}
    )

    # Test set_repo with local repository
    bf.set_brewfile_repo()
    with Path(file).open() as f:
        assert f.read() == f'git file://{repo}'
    with Path(local_repo / 'README.md').open() as f:
        assert (
            f.read()
            == """# repo

Package list for [homebrew](http://brew.sh/).

Managed by [homebrew-file](https://github.com/rcmdnk/homebrew-file)."""
        )

    with Path(repo / 'Brewfile').open() as f:
        assert f.read() == ''
    with Path(local_repo / 'Brewfile').open() as f:
        assert f.read() == ''

    with Path(local_repo / 'Brewfile').open('w') as f:
        f.write('test')
    bf.repomgr('push')
    with Path(repo / 'Brewfile').open() as f:
        assert f.read() == 'test'

    with Path(repo / 'Brewfile').open('w') as f:
        f.write('test2')
    bf.helper.proc('git commit -a -m "test2"', cwd=repo)
    bf.repomgr('pull')
    with Path(local_repo / 'Brewfile').open() as f:
        assert f.read() == 'test2'


def test_install_error_handling(
    tmp_path: Path,
) -> None:
    file = tmp_path / 'Brewfile'
    bf = BrewFile(opt={'input': file, 'yn': True})
    # Test non-existent package
    with Path(file).open('w') as f:
        f.write('brew nonexistent-package')

    with pytest.raises(CmdError) as excinfo:
        bf.install()
    assert 'Failed at command:' in str(excinfo.value)
    assert 'install nonexistent-package' in str(excinfo.value)


def test_before_after_commands(
    tmp_path: Path,
) -> None:
    # Test before/after commands
    file = tmp_path / 'Brewfile'
    test_before_file = tmp_path / 'before.txt'
    test_after_file = tmp_path / 'after.txt'
    with Path(file).open('w') as f:
        f.write(f"""
before touch {test_before_file}
after touch {test_after_file}
""")
    bf = BrewFile(opt={'input': file, 'yn': True})
    assert not Path(test_before_file).exists()
    assert not Path(test_after_file).exists()
    bf.install()
    assert Path(test_before_file).exists()
    assert Path(test_after_file).exists()

    # Check if the commands are remaining in the Brewfile after initialization
    bf.initialize()
    with Path(file).open() as f:
        content = f.read()
        assert f'before touch {test_before_file}' in content
        assert f'after touch {test_after_file}' in content


def test_edit_brewfile(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    editor_script = Path(__file__).parent / 'scripts' / 'test_editor.sh'
    monkeypatch.setenv('HOMEBREW_BREWFILE_EDITOR', str(editor_script))
    file = tmp_path / 'Brewfile'
    file.touch()
    bf = BrewFile(opt={'input': str(file)})
    bf.edit_brewfile()
    with Path(file).open() as f:
        assert f.read() == 'test content\n'


def test_clean_non_request(bf: BrewFile) -> None:
    bf.opt['dryrun'] = True
    bf.clean_non_request()


@pytest.mark.parametrize(
    ('app', 'token'),
    [
        ('/App/Foo.app', 'foo'),
        ('/App/--A B  C--D+E@f-9.app', 'a-b-c-dpluseatf9'),
        ('Foo Bar.app', 'foo-bar'),
        ('C++ @App++.app', 'cplusplus-atappplusplus'),
        ('123Foo.app', '123foo'),
    ],
)
def test_generate_cask_token(bf: BrewFile, app: str, token: str) -> None:
    assert bf.generate_cask_token(app) == token


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
