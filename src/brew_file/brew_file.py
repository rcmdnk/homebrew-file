from __future__ import annotations

import copy
import logging
import os
import re
import shlex
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from types import TracebackType
from typing import Any, Literal, cast
from urllib.parse import quote

from .brew_helper import BrewHelper
from .brew_info import BrewInfo
from .info import __prog__
from .utils import OpenWrapper, expandpath, home_tilde, is_mac, to_bool, to_num

CaskInfo = dict[str, tuple[str, str]]
CaskListInfo = dict[str, list[tuple[str, str]]]


@dataclass
class BrewFile:
    """Main class of Brew-file."""

    opt: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.log = logging.getLogger(__name__)

        # Make helper
        self.helper = BrewHelper(self.opt)

        # Check Homebrew
        self.check_brew_cmd()

        # Set full opt
        for k, v in self.default_opt().items():
            if k not in self.opt:
                self.opt[k] = v

        # Set other initial variables
        self.int_opts: list[str] = []
        self.float_opts: list[str] = []

        # fix up opt
        self.set_args()

    def get_input_path(self) -> Path:
        input_path = None
        xdg_config_home = os.getenv('XDG_CONFIG_HOME')
        if xdg_config_home is not None:
            input_path = Path(xdg_config_home) / 'brewfile/Brewfile'
            if input_path.is_file():
                return input_path
        home_config = Path(os.environ['HOME']) / '.config/brewfile/Brewfile'
        if home_config.is_file():
            return home_config
        if input_path is None:
            input_path = home_config

        home_brewfile = Path(os.environ['HOME']) / '/.brewfile/Brewfile'
        if home_brewfile.is_file():
            return home_brewfile
        return input_path

    def parse_env_opts(
        self,
        env_var: str,
        base_opts: dict[str, Any] | None = None,
    ) -> dict[str, str]:
        """Return a dictionary parsed from an environment variable."""
        opts: dict[str, Any] = {}
        if base_opts is not None:
            opts.update(base_opts)

        env_opts = os.getenv(env_var, None)
        if env_opts:
            user_opts = dict(
                pair.partition('=')[::2] for pair in env_opts.split()
            )

            if user_opts:
                opts.update(user_opts)
            else:
                self.log.warning(
                    '{env_var}: "{env_opts}" is not a proper format.',
                )
                self.log.warning('Ignoring the value.\n')
        return opts

    def default_opt(self) -> dict[str, Any]:
        opt: dict[str, Any] = {}
        opt['verbose'] = os.getenv('HOMEBREW_BREWFILE_VERBOSE', 'info')
        opt['command'] = ''
        opt['input'] = Path(os.getenv('HOMEBREW_BREWFILE', ''))
        if not opt['input'].name:
            opt['input'] = self.get_input_path()
        opt['backup'] = os.getenv('HOMEBREW_BREWFILE_BACKUP', '')
        opt['form'] = None
        opt['leaves'] = to_bool(os.getenv('HOMEBREW_BREWFILE_LEAVES', ''))
        opt['on_request'] = to_bool(
            os.getenv('HOMEBREW_BREWFILE_ON_REQUEST', ''),
        )
        opt['top_packages'] = os.getenv('HOMEBREW_BREWFILE_TOP_PACKAGES', '')
        opt['fetch_head'] = to_bool(
            os.getenv('HOMEBREW_BREWFILE_FETCH_HEAD', ''),
        )
        opt['repo'] = ''
        opt['no_repo'] = False
        opt['noupgradeatupdate'] = False
        opt['link'] = True
        opt['caskonly'] = False
        opt['dryrun'] = False
        opt['initialized'] = False
        opt['homebrew_tap_prefix'] = 'homebrew/'
        opt['core_repo'] = f'{opt["homebrew_tap_prefix"]}core'
        opt['cask_repo'] = f'{opt["homebrew_tap_prefix"]}cask'
        opt['reattach_formula'] = 'reattach-to-user-namespace'
        opt['mas_formula'] = 'mas'
        opt['whalebrew_formula'] = 'whalebrew'
        opt['vscode_formula'] = 'visual-studio-code'
        opt['cursor_formula'] = 'cursor'
        opt['codium_formula'] = 'vscodium'
        opt['my_editor'] = os.getenv(
            'HOMEBREW_BREWFILE_EDITOR',
            os.getenv('EDITOR', 'vim'),
        )
        opt['brew_cmd'] = ''
        opt['mas_cmd'] = 'mas'
        opt['is_mas_cmd'] = 0
        opt['mas_cmd_installed'] = False
        opt['reattach_cmd_installed'] = False
        opt['whalebrew_cmd'] = 'whalebrew'
        opt['is_whalebrew_cmd'] = 0
        opt['whalebrew_cmd_installed'] = False
        opt['vscode_cmd'] = 'code'
        opt['is_vscode_cmd'] = 0
        opt['vscode_cmd_installed'] = False
        opt['cursor_cmd'] = 'cursor'
        opt['is_cursor_cmd'] = 0
        opt['cursor_cmd_installed'] = False
        opt['codium_cmd'] = 'codium'
        opt['is_codium_cmd'] = 0
        opt['codium_cmd_installed'] = False
        opt['docker_running'] = 0
        opt['args'] = []
        opt['yn'] = False
        opt['brew_packages'] = ''
        opt['homebrew_ruby'] = False

        # Check Homebrew variables
        # Boolean HOMEBREW variable should be True if other than empty is set, including '0'
        opt['api'] = not os.getenv('HOMEBREW_NO_INSTALL_FROM_API', '')
        opt['cache'] = self.helper.brew_val('cache')
        opt['caskroom'] = self.helper.brew_val('prefix') + '/Caskroom'
        cask_opts = self.parse_env_opts(
            'HOMEBREW_CASK_OPTS',
            {'--appdir': '', '--fontdir': ''},
        )
        opt['appdir'] = (
            cask_opts['--appdir'].rstrip('/')
            if cask_opts['--appdir'] != ''
            else os.environ['HOME'] + '/Applications'
        )
        opt['appdirlist'] = [
            '/Applications',
            os.environ['HOME'] + '/Applications',
        ]
        if opt['appdir'].rstrip('/') not in opt['appdirlist']:
            opt['appdirlist'].append(opt['appdir'])
        opt['appdirlist'] += [
            x.rstrip('/') + '/Utilities' for x in opt['appdirlist']
        ]
        opt['appdirlist'] = [x for x in opt['appdirlist'] if Path(x).is_dir()]
        # fontdir may be used for application search, too
        opt['fontdir'] = cask_opts['--fontdir']

        opt['appstore'] = to_num(os.getenv('HOMEBREW_BREWFILE_APPSTORE', '-1'))
        opt['no_appstore'] = False
        opt['full_name'] = to_bool(
            os.getenv('HOMEBREW_BREWFILE_FULL_NAME', '')
        )
        opt['all_files'] = False

        opt['whalebrew'] = to_num(
            os.getenv('HOMEBREW_BREWFILE_WHALEBREW', '0'),
        )
        opt['vscode'] = to_num(os.getenv('HOMEBREW_BREWFILE_VSCODE', '0'))
        opt['cursor'] = to_num(os.getenv('HOMEBREW_BREWFILE_CURSOR', '0'))
        opt['codium'] = to_num(os.getenv('HOMEBREW_BREWFILE_CODIUM', '0'))

        opt['read'] = False

        return opt

    def set_input(self, file: str | Path) -> None:
        self.opt['input'] = Path(file)
        self.brewinfo = BrewInfo(self.helper, self.opt['input'])
        self.brewinfo_ext: list[BrewInfo] = []
        self.brewinfo_main = self.brewinfo

    def banner(self, text: str, debug_out: bool = False) -> None:
        width = 0
        for line in text.split('\n'):
            width = max(width, len(line))
        output = f'\n{"#" * width}\n{text}\n{"#" * width}\n'
        if debug_out:
            self.log.debug(output)
        else:
            self.log.info(output)

    @dataclass
    class DryrunBanner:
        """Dryrun banner context manager."""

        brewfile: BrewFile

        def __enter__(self) -> None:
            if self.brewfile.opt['dryrun']:
                self.brewfile.banner('# This is dry run.')

        def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            traceback: TracebackType | None,
        ) -> None:
            if self.brewfile.opt['dryrun']:
                self.brewfile.banner('# This is dry run.')

    def set_verbose(self, verbose: str | None = None) -> None:
        if verbose is None:
            self.opt['verbose'] = os.getenv(
                'HOMEBREW_BREWFILE_VERBOSE',
                'info',
            )
        else:
            self.opt['verbose'] = verbose
        # Keep compatibility with old verbose
        if self.opt['verbose'] == '0':
            self.opt['verbose'] = 'debug'
        elif self.opt['verbose'] == '1':
            self.opt['verbose'] = 'info'
        elif self.opt['verbose'] == '2':
            self.opt['verbose'] = 'error'

        if self.log.parent and self.log.parent.name != 'root':
            self.log.parent.setLevel(
                getattr(logging, self.opt['verbose'].upper()),
            )
        else:
            self.log.setLevel(getattr(logging, self.opt['verbose'].upper()))

    def set_args(self, **kw: str) -> None:
        """Set arguments."""
        self.opt.update(kw)

        self.set_verbose(self.opt.get('verbose', None))
        for k in self.int_opts:
            self.opt[k] = int(self.opt[k])
        for k in self.float_opts:
            self.opt[k] = float(self.opt[k])

        # fix appstore option
        appstore = 1
        if self.opt['appstore'] != -1:
            appstore = self.opt['appstore']
        elif self.opt['no_appstore']:
            appstore = 0
        self.opt['appstore'] = to_num(appstore)

        self.set_input(self.opt['input'])

    def ask_yn(self, question: str) -> bool:
        """Ask yes/no question."""
        if self.opt['yn']:
            self.log.info(f'{question} [y/n]: y')
            return True

        yes = ['yes', 'y', '']
        no = ['no', 'n']

        yn = input(f'{question} [y/n]: ').lower()
        while True:
            if yn in yes:
                return True
            if yn in no:
                return False
            yn = input('Answer with yes (y) or no (n): ').lower()

    def read_all(self, force: bool = False) -> None:
        if not force and self.opt['read']:
            return
        self.brewinfo_ext = [self.brewinfo]
        main = self.read(self.brewinfo, is_main=True)
        if not main:
            msg = 'Cannot find main Brewfile.'
            raise RuntimeError(msg)
        self.brewinfo_main = main
        self.brewinfo_ext.remove(self.brewinfo_main)
        for cmd in [
            'mas',
            'reattach',
            'whalebrew',
            'vscode',
            'cursor',
            'codium',
        ]:
            if self.opt[f'{cmd}_cmd_installed']:
                p = Path(self.opt[f'{cmd}_formula']).name
                if p not in self.get_list('brew_input'):
                    self.brewinfo_main.brew_input.append(p)
                    self.brewinfo_main.brew_opt_input[p] = ''
        self.opt['read'] = True

    def read(
        self,
        brewinfo: BrewInfo,
        is_main: bool = False,
    ) -> BrewInfo | None:
        main = brewinfo if is_main else None
        files = brewinfo.get_files()
        for f in files['ext']:
            is_next_main = f in files['main']
            path = expandpath(f)
            if path.is_absolute():
                b = BrewInfo(self.helper, path)
            else:
                b = BrewInfo(self.helper, brewinfo.get_dir() / path)
            self.brewinfo_ext.append(b)
            if main is not None and is_next_main:
                main = b
                main_tmp = self.read(b, True)
            else:
                main_tmp = self.read(b, False)
            if main_tmp is not None:
                main = main_tmp
        return main

    def list_to_main(self) -> None:
        if self.brewinfo == self.brewinfo_main:
            return
        self.brewinfo_main.add_to_list('brew_list', self.brewinfo.brew_list)
        self.brewinfo_main.add_to_list(
            'brew_full_list',
            self.brewinfo.brew_list,
        )
        self.brewinfo_main.add_to_list('tap_list', self.brewinfo.tap_list)
        self.brewinfo_main.add_to_list('cask_list', self.brewinfo.cask_list)
        self.brewinfo_main.add_to_list(
            'cask_nocask_list',
            self.brewinfo.cask_nocask_list,
        )
        self.brewinfo_main.add_to_list(
            'appstore_list',
            self.brewinfo.appstore_list,
        )
        self.brewinfo_main.add_to_list(
            'whalebrew_list',
            self.brewinfo.whalebrew_list,
        )
        self.brewinfo_main.add_to_list(
            'vscode_list',
            self.brewinfo.vscode_list,
        )
        self.brewinfo_main.add_to_list(
            'cursor_list',
            self.brewinfo.cursor_list,
        )
        self.brewinfo_main.add_to_list(
            'codium_list',
            self.brewinfo.codium_list,
        )
        self.brewinfo_main.add_to_dict(
            'brew_opt_list',
            self.brewinfo.brew_opt_list,
        )

    def input_to_list(self, only_ext: bool = False) -> None:
        if not only_ext:
            self.brewinfo_main.input_to_list()
        for b in self.brewinfo_ext:
            b.input_to_list()

    def write(self, debug_out: bool = False) -> None:
        self.banner(
            f'# Initialize {self.brewinfo_main.file}',
            debug_out=debug_out,
        )
        self.brewinfo_main.write()
        for b in self.brewinfo_ext:
            self.banner(f'# Initialize {b.file}', debug_out=debug_out)
            b.write()

    def get_list(self, name: str, only_ext: bool = False) -> set[str]:
        list_copy = [] if only_ext else self.brewinfo_main.get_list(name)
        for b in self.brewinfo_ext:
            list_copy += b.get_list(name)
        return set(list_copy)

    def get_dict(self, name: str, only_ext: bool = False) -> dict[str, str]:
        dict_copy = {} if only_ext else self.brewinfo_main.get_dict(name)
        for b in self.brewinfo_ext:
            dict_copy.update(b.get_dict(name))
        return dict_copy

    def get_non_alias_input(self, package_type: str) -> set[str]:
        if package_type == 'formulae':
            list_name = 'brew_input'
        elif package_type == 'casks':
            list_name = 'cask_input'
        aliases = self.helper.get_aliases(package_type, flat=True)
        packages = []
        for p in self.get_list(list_name):
            if p in aliases:
                packages.append(aliases[p])
            else:
                packages.append(p)
        return set(packages)

    def remove_pack(self, name: str, package: str) -> None:
        if package in self.brewinfo_main.get_list(name):
            self.brewinfo_main.remove(name, package)
        else:
            for b in self.brewinfo_ext:
                if package in b.get_list(name):
                    b.remove(name, package)

    def repo_name(self) -> str:
        return self.opt['repo'].split('/')[-1].split('.git')[0]

    def user_name(self) -> str:
        user = ''
        repo_split = self.opt['repo'].split('/')
        if len(repo_split) > 1:
            user = repo_split[-2].split(':')[-1]
        if not user:
            _, lines = self.helper.proc(
                'git config --get github.user',
                print_cmd=False,
                print_out=False,
                exit_on_err=False,
                separate_err=False,
            )
            if lines:
                user = lines[0]
            else:
                _, lines = self.helper.proc(
                    'git config --get user.name',
                    print_cmd=False,
                    print_out=False,
                    exit_on_err=False,
                    separate_err=False,
                )
                user = lines[0] if lines else ''
            if not user:
                msg = 'Can not find git (github) user name'
                raise RuntimeError(msg)
        return user

    def input_dir(self) -> Path:
        return self.opt['input'].parent

    def input_file(self) -> str:
        return self.opt['input'].name

    def repo_file(self) -> Path:
        """Return the Brewfile path for the repository."""
        return Path(
            self.input_dir(),
            self.user_name() + '_' + self.repo_name(),
            self.input_file(),
        )

    def init_repo(self) -> None:
        dirname = Path(self.brewinfo.get_dir())
        _, branches = self.helper.proc(
            'git branch',
            print_cmd=False,
            print_out=False,
            exit_on_err=True,
            separate_err=True,
            cwd=dirname,
        )
        if branches:
            return

        self.log.info('Initialize the repository with README.md/Brewfile.')
        readme = dirname / 'README.md'
        if not readme.exists():
            with Path(readme).open('w') as f:
                f.write(
                    '# ' + self.repo_name() + '\n\n'
                    'Package list for [homebrew](http://brew.sh/).\n\n'
                    'Managed by '
                    '[homebrew-file](https://github.com/rcmdnk/homebrew-file).',
                )
        self.brewinfo.file.touch()

        if self.check_gitconfig():
            _ = self.helper.proc('git add -A', cwd=dirname)
            _ = self.helper.proc(
                ['git', 'commit', '-m', '"Prepared by ' + __prog__ + '"'],
                cwd=dirname,
            )
            _, lines = self.helper.proc(
                'git branch --show-current',
                cwd=dirname,
                exit_on_err=False,
            )
            branch = lines[0]
            self.helper.proc(
                f'git push -u origin {branch}',
                cwd=dirname,
            )

    def clone_repo(self, exit_on_err: bool = True) -> bool:
        ret, _ = self.helper.proc(
            f"git clone {self.opt['repo']} '{self.brewinfo.get_dir()}'",
            print_cmd=True,
            print_out=True,
            exit_on_err=False,
        )
        if ret != 0:
            if exit_on_err:
                msg = (
                    f'Can not clone {self.opt["repo"]}.\n'
                    f'please check the repository, or reset with\n'
                    f'    $ {__prog__} set_repo'
                )
                raise RuntimeError(msg)
            return False
        self.init_repo()
        return True

    def check_github_repo(self) -> None:
        """Check GitHub repository."""
        # Check if the repository already exists or not.
        if self.clone_repo(exit_on_err=False):
            return

        # Create new repository #
        msg = (
            f"GitHub repository: {self.user_name()}/{self.repo_name()} doesn't exist.\n"
            'Please create the repository first, then try again'
        )
        raise RuntimeError(msg)

    def check_local_repo(self) -> None:
        dirname = self.opt['repo'].replace('file://', '')
        Path(dirname).mkdir(parents=True, exist_ok=True)
        _ = self.helper.proc('git init', cwd=dirname)
        _ = self.helper.proc(
            'git config --local receive.denyCurrentBranch updateInstead',
            cwd=dirname,
        )
        self.clone_repo()

    def check_repo(self) -> None:
        """Check input file for Git repository."""
        # Check input file
        if not self.opt['input'].exists():
            return

        self.brewinfo.file = self.opt['input']

        # Check input file if it points repository or not
        self.opt['repo'] = ''
        with Path(self.opt['input']).open() as f:
            lines = f.readlines()
        for line in lines:
            if re.match(' *git ', line) is None:
                continue
            git_line = line.split()
            if len(git_line) > 1:
                self.opt['repo'] = git_line[1]
                break
        if self.opt['repo'] == '':
            return

        # Check repository name and add git@github.com: if necessary
        if (
            '@' not in self.opt['repo']
            and not self.opt['repo'].startswith('git://')
            and not self.opt['repo'].startswith('http://')
            and not self.opt['repo'].startswith('file://')
            and not self.opt['repo'].startswith('/')
        ):
            self.opt['repo'] = (
                'git@github.com:' + self.user_name() + '/' + self.repo_name()
            )

        # Set Brewfile in the repository
        self.brewinfo.file = self.repo_file()

        # If repository does not have a branch, make it
        if self.brewinfo.check_dir():
            self.init_repo()
            return

        # Check and prepare repository
        if 'github' in self.opt['repo']:
            self.check_github_repo()
        elif self.opt['repo'].startswith('file://') or self.opt[
            'repo'
        ].startswith('/'):
            self.check_local_repo()
        else:
            self.clone_repo()

    def check_gitconfig(self) -> bool:
        if self.opt['repo'].startswith('git://') or self.opt[
            'repo'
        ].startswith('http'):
            self.log.info(
                f'You are using repository of {self.opt["repo"]}\n'
                'Use ssh protocol to push your Brewfile update.',
            )
            return False
        _, name = self.helper.proc(
            'git config user.name',
            print_cmd=False,
            print_out=False,
            exit_on_err=False,
            separate_err=True,
        )
        _, email = self.helper.proc(
            'git config user.email',
            print_cmd=False,
            print_out=False,
            exit_on_err=False,
            separate_err=True,
        )
        if not name or not email:
            self.log.warning(
                "You don't have user/email information in your .gitconfig.\n"
                'To commit and push your update, run\n'
                '  git config --global user.email "you@example.com"\n'
                '  git config --global user.name "Your Name"\n'
                'and try again.',
            )
            return False
        return True

    def repomgr(self, cmd: str = 'pull') -> None:
        """Manage repository."""
        # Check the repository
        if self.opt['repo'] == '':
            msg = (
                f'Please set a repository, or reset with:\n'
                f'$ {__prog__} set_repo\n'
            )
            raise RuntimeError(msg)

        # Clone if it doesn't exist
        if not self.brewinfo.check_dir():
            self.clone_repo()

        # pull/push
        dirname = self.brewinfo.get_dir()

        ret, lines = self.helper.proc(
            'git status -s -uno',
            print_cmd=False,
            print_out=False,
            exit_on_err=True,
            cwd=dirname,
        )
        if ret != 0:
            msg = '\n'.join(lines)
            raise RuntimeError(msg)
        if lines and self.check_gitconfig():
            _ = self.helper.proc(
                'git add -A',
                dryrun=self.opt['dryrun'],
                cwd=dirname,
            )
            _ = self.helper.proc(
                ['git', 'commit', '-m', '"Update the package list"'],
                exit_on_err=False,
                dryrun=self.opt['dryrun'],
                cwd=dirname,
            )

        _ = self.helper.proc(
            f'git {cmd}',
            dryrun=self.opt['dryrun'],
            cwd=dirname,
        )

    def brew_cmd(self) -> None:
        noinit = False
        if self.opt['args'] and 'noinit' in self.opt['args']:
            noinit = True
            self.opt['args'].remove('noinit')

        exe = ['brew']
        cmd = self.opt['args'][0] if self.opt['args'] else ''
        subcmd = self.opt['args'][1] if len(self.opt['args']) > 1 else ''
        args = self.opt['args']
        if cmd == 'mas':
            exe = ['mas']
            self.opt['args'].pop(0)
            if subcmd == 'uninstall':
                exe = ['sudo', 'mas']
            package = self.opt['args'][1:] if len(self.opt['args']) > 1 else ''
            if self.check_mas_cmd(True) != 1:
                msg = "\n'mas' command is not available.\n"
                if package:
                    msg += f"Please install 'mas' or manage {shlex.join(package)} manually"
                raise RuntimeError(msg)
        if cmd == 'whalebrew':
            exe = ['whalebrew']
            self.opt['args'].pop(0)
            if subcmd == 'uninstall':
                self.opt['args'].append('-y')
            if self.check_whalebrew_cmd(True) != 1:
                msg = "\n'whalebrew' command is not available.\n"
                raise RuntimeError(msg)
        if cmd == 'code':
            exe = ['code']
            self.opt['args'].pop(0)
            if self.check_vscode_cmd(True) != 1:
                msg = "\n'code' command (for VSCode) is not available.\n"
                raise RuntimeError(msg)
        if cmd == 'cursor':
            exe = ['cursor']
            self.opt['args'].pop(0)
            if self.check_cursor_cmd(True) != 1:
                msg = "\n'cursor' command is not available.\n"
                raise RuntimeError(msg)
        if cmd == 'codium':
            exe = ['codium']
            self.opt['args'].pop(0)
            if self.check_codium_cmd(True) != 1:
                msg = "\n'codium' command (for VSCodium) is not available.\n"
                raise RuntimeError(msg)

        ret, lines = self.helper.proc(
            exe + self.opt['args'],
            print_cmd=False,
            print_out=True,
            exit_on_err=False,
            dryrun=self.opt['dryrun'],
        )
        if self.opt['dryrun']:
            return

        if (
            noinit
            or (cmd == 'mas' and self.opt['appstore'] != 1)
            or (cmd == 'whalebrew' and self.opt['whalebrew'] != 1)
            or (cmd == 'code' and self.opt['vscode'] != 1)
            or (cmd == 'cursor' and self.opt['cursor'] != 1)
            or (cmd == 'codium' and self.opt['codium'] != 1)
            or (
                ret != 0
                and 'Not installed' not in ' '.join(lines)
                and 'No installed keg or cask with the name'
                not in ' '.join(lines)
            )
        ):
            return

        if cmd in ['cask']:
            args = self.opt['args'][2:]
        else:
            args = self.opt['args'][1:]
        nargs = len(args)

        if (
            cmd
            not in [
                'instal',
                'install',
                'reinstall',
                'tap',
                'rm',
                'remove',
                'uninstall',
                'untap',
                'cask',
                'mas',
                'whalebrew',
                'code',
                'cursor',
                'codium',
            ]
            or nargs == 0
            or (
                cmd == 'cask'
                and subcmd
                not in ['instal', 'install', 'rm', 'remove', 'uninstall']
            )
            or (
                cmd == 'mas'
                and subcmd not in ['purchase', 'install', 'uninstall']
            )
            or (cmd == 'whalebrew' and subcmd not in ['install', 'uninstall'])
            or (
                cmd == 'code'
                and subcmd
                not in ['--install-extension', '--uninstall-extension']
            )
            or (
                cmd == 'cursor'
                and subcmd
                not in ['--install-extension', '--uninstall-extension']
            )
            or (
                cmd == 'codium'
                and subcmd
                not in ['--install-extension', '--uninstall-extension']
            )
        ):
            # Not install/remove command, no init.
            return

        _ = self.initialize(check=False, debug_out=True)

    def add_path(self) -> None:
        env_path = os.getenv('PATH', '')
        paths = env_path.split(':')
        for path in [
            '/home/linuxbrew/.linuxbrew/bin',
            os.getenv('HOME', '') + '/.linuxbrew/bin',
            '/opt/homebrew/bin',
            '/usr/local/bin',
        ]:
            if path not in paths:
                os.environ['PATH'] = path + ':' + env_path

    def which_brew(self) -> bool:
        ret, cmd = self.helper.proc(
            'which brew',
            print_cmd=False,
            print_out=False,
            exit_on_err=False,
        )
        if ret == 0:
            self.opt['brew_cmd'] = cmd[0]
            self.opt['is_brew_cmd'] = True
            return True
        return False

    def check_brew_cmd(self) -> bool:
        """Check Homebrew."""
        if self.opt.get('is_brew_cmd', False):
            return True

        if self.which_brew():
            return True

        self.add_path()
        if self.which_brew():
            return True

        self.log.info('Homebrew has not been installed, install now...')
        with tempfile.NamedTemporaryFile() as f:
            cmd = (
                f'curl -o {f.name} -O https://raw.githubusercontent.com/'
                'Homebrew/install/master/install.sh'
            )
            _ = self.helper.proc(
                cmd,
                print_cmd=True,
                print_out=True,
                exit_on_err=False,
            )
            cmd = f'bash {f.name}'
            _ = self.helper.proc(
                cmd,
                print_cmd=True,
                print_out=True,
                exit_on_err=False,
            )
        if not self.which_brew():
            return False
        ret, lines = self.helper.proc(
            'brew doctor',
            print_cmd=True,
            print_out=True,
            exit_on_err=False,
        )
        if ret != 0:
            for line in lines:
                self.log.info(line)
            self.log.warning(
                '\n\nCheck brew environment and fix problems if necessary.\n'
                '# You can check by:\n'
                '#     $ brew doctor',
            )
        return True

    def check_cmd(
        self,
        flag: str,
        cmd: str,
        formula: str,
        install: bool = False,
    ) -> Literal[-2, -1, 0, 1]:
        """Check command is installed or not."""
        if self.opt[flag] != 0:
            return self.opt[flag]

        if shutil.which(cmd) is None:
            if not install:
                return self.opt[flag]
            self.log.info(f'{formula} has not been installed.')
            ret, _ = self.helper.proc(
                ['brew', 'install', formula],
                print_cmd=True,
                print_out=True,
                exit_on_err=False,
            )
            if ret != 0:
                self.log.error(f'\nFailed to install {formula}\n')
                self.opt[flag] = -1
                return self.opt[flag]
            p = Path(formula).name
            if p not in self.get_list('brew_list'):
                self.brewinfo.brew_list.append(p)
                self.brewinfo.brew_opt_list[p] = ''

        if shutil.which(cmd) is None:
            msg = f'Failed to prepare {cmd} command.'
            raise RuntimeError(msg)

        self.opt[flag] = 1
        return self.opt[flag]

    def check_mas_cmd(self, install: bool = False) -> Literal[-2, -1, 0, 1]:
        """Check mas is installed or not."""
        if self.opt['is_mas_cmd'] != 0:
            return self.opt['is_mas_cmd']

        if not is_mac():
            msg = 'mas is not available on Linux!'
            raise RuntimeError(msg)

        _, lines = self.helper.proc(
            'sw_vers -productVersion',
            print_cmd=False,
            print_out=False,
            exit_on_err=False,
        )
        sw_vers = lines[0].split('.')
        if int(sw_vers[0]) < 10 or (
            int(sw_vers[0]) == 10 and int(sw_vers[1]) < 11
        ):
            self.log.warning('You are using older OS X. mas can not be used.')
            self.opt['is_mas_cmd'] = -1
            return self.opt['is_mas_cmd']

        cmd_ret = self.check_cmd(
            'is_mas_cmd',
            self.opt['mas_cmd'],
            self.opt['mas_formula'],
            install,
        )
        if cmd_ret != 1:
            return cmd_ret

        # # Disable check until this issue is solved:
        # # https://github.com/mas-cli/mas#%EF%B8%8F-known-issues
        # if self.helper.proc(self.opt["mas_cmd"] + " account", print_cmd=False,
        #             print_out=False, exit_on_err=False)[0] != 0:
        #    msg = "Please sign in to the App Store."
        #    raise RuntimeError(msg)

        is_tmux = os.getenv('TMUX', '')
        if is_tmux != '':
            ret, _ = self.helper.proc(
                'type reattach-to-user-namespace',
                print_cmd=False,
                print_out=False,
                exit_on_err=False,
            )
            if ret != 0:
                f'You need {self.opt["reattach_formula"]} in tmux. Installing it.'
                ret, _ = self.helper.proc(
                    ['brew', 'install', self.opt['reattach_formula']],
                    print_cmd=True,
                    print_out=True,
                    exit_on_err=False,
                )
                if ret != 0:
                    self.log.error(
                        f'\nFailed to install {self.opt["reattach_formula"]}\n',
                    )
                    self.opt['is_mas_cmd'] = -1
                    return self.opt['is_mas_cmd']
                p = Path(self.opt['reattach_formula']).name
                if p not in self.get_list('brew_list'):
                    self.brewinfo.brew_list.append(p)
                    self.brewinfo.brew_opt_list[p] = ''
                self.opt['reattach_cmd_installed'] = True
            self.opt['mas_cmd'] = 'reattach-to-user-namespace mas'

        return self.opt['is_mas_cmd']

    def check_whalebrew_cmd(
        self,
        install: bool = False,
    ) -> Literal[-2, -1, 0, 1]:
        """Check whalebrew is installed or not."""
        if self.opt['is_whalebrew_cmd'] != 0:
            return self.opt['is_whalebrew_cmd']

        return self.check_cmd(
            'is_whalebrew_cmd',
            self.opt['whalebrew_cmd'],
            self.opt['whalebrew_formula'],
            install,
        )

    def check_vscode_cmd(self, install: bool = False) -> Literal[-2, -1, 0, 1]:
        """Check code (for VSCode) is installed or not."""
        if self.opt['is_vscode_cmd'] != 0:
            return self.opt['is_vscode_cmd']

        return self.check_cmd(
            'is_vscode_cmd',
            self.opt['vscode_cmd'],
            self.opt['vscode_formula'],
            install,
        )

    def check_cursor_cmd(self, install: bool = False) -> Literal[-2, -1, 0, 1]:
        """Check cursor is installed or not."""
        if self.opt['is_cursor_cmd'] != 0:
            return self.opt['is_cursor_cmd']

        return self.check_cmd(
            'is_cursor_cmd',
            self.opt['cursor_cmd'],
            self.opt['cursor_formula'],
            install,
        )

    def check_codium_cmd(self, install: bool = False) -> Literal[-2, -1, 0, 1]:
        """Check codium is installed or not."""
        if self.opt['is_codium_cmd'] != 0:
            return self.opt['is_codium_cmd']

        return self.check_cmd(
            'is_codium_cmd',
            self.opt['codium_cmd'],
            self.opt['codium_formula'],
            install,
        )

    def check_docker_running(self) -> Literal[-2, -1, 0, 1]:
        """Check if Docker is running."""
        if self.opt['docker_running'] != 0:
            return self.opt['docker_running']
        ret, _ = self.helper.proc(
            'type docker',
            print_cmd=False,
            print_out=False,
            exit_on_err=False,
        )
        if ret != 0:
            self.opt['docker_running'] = -1
            return self.opt['docker_running']
        ret, _ = self.helper.proc(
            'docker ps',
            print_cmd=False,
            print_out=False,
            exit_on_err=False,
        )
        if ret != 0:
            self.opt['docker_running'] = -2
            return self.opt['docker_running']
        self.opt['docker_running'] = 1
        return self.opt['docker_running']

    def get_appstore_dict(self) -> dict[str, list[str]]:
        apps: dict[str, list[str]] = {}
        _, apps_tmp = self.helper.proc(
            "mdfind 'kMDItemAppStoreHasReceipt=1'",
            print_cmd=False,
            print_out=False,
        )
        for a in apps_tmp:
            if not a.endswith('.app'):
                self.log.warning(f'Incorrect app name in mdfind: {a}')
                continue
            if not Path(a).is_dir():
                self.log.warning(f"App doesn't exist: {a}")
                continue
            _, lines = self.helper.proc(
                f'mdls -attr kMDItemAppStoreAdamID -attr kMDItemVersion {shlex.quote(a)}',
                print_cmd=False,
                print_out=False,
            )
            app = {
                x.split('=')[0].strip(): x.split('=')[1].strip() for x in lines
            }
            app_id = app['kMDItemAppStoreAdamID']
            if app_id != '(null)':
                app_name = a.split('/')[-1].split('.app')[0]
                app_version = app['kMDItemVersion'].strip('"')
                apps[app_name] = [app_id, f'({app_version})']
        return apps

    def get_appstore_list(self) -> list[str]:
        return [
            f'{v[0]} {k} {v[1]}' for k, v in self.get_appstore_dict().items()
        ]

    def get_whalebrew_list(self) -> list[str]:
        if self.opt['whalebrew'] != 1:
            return []
        if self.check_whalebrew_cmd(False) != 1:
            return []
        _, lines = self.helper.proc(
            f'{self.opt["whalebrew_cmd"]} list',
            print_cmd=False,
            print_out=False,
            exit_on_err=False,
        )
        return [x.split()[1] for x in lines if x.split()[0] != 'COMMAND']

    def get_vscode_list(self) -> list[str]:
        if self.opt['vscode'] != 1:
            return []
        if self.check_vscode_cmd(False) != 1:
            return []
        # Remove stderr output for SecCodeCheckValidity issue:
        # https://github.com/microsoft/vscode/issues/204085
        # https://github.com/microsoft/vscode/issues/204447
        _, lines = self.helper.proc(
            f'{self.opt["vscode_cmd"]} --list-extensions',
            print_cmd=False,
            print_out=False,
            exit_on_err=False,
            separate_err=True,
            print_err=False,
        )
        return lines

    def get_cursor_list(self) -> list[str]:
        if self.opt['cursor'] != 1:
            return []
        if self.check_cursor_cmd(False) != 1:
            return []
        _, lines = self.helper.proc(
            f'{self.opt["cursor_cmd"]} --list-extensions',
            print_cmd=False,
            print_out=False,
            exit_on_err=False,
            separate_err=True,
            print_err=False,
        )
        return lines

    def get_codium_list(self) -> list[str]:
        if self.opt['codium'] != 1:
            return []
        if self.check_codium_cmd(False) != 1:
            return []
        _, lines = self.helper.proc(
            f'{self.opt["codium_cmd"]} --list-extensions',
            print_cmd=False,
            print_out=False,
            exit_on_err=False,
            separate_err=True,
            print_err=False,
        )
        return lines

    def get_installed_formulae(self) -> list[str]:
        full_list = self.helper.get_formula_list()
        if not self.brewinfo.brew_full_list:
            self.brewinfo.brew_full_list.extend(full_list)
        if self.opt['leaves']:
            packages = self.helper.get_leaves(
                on_request=self.opt['on_request'],
            )
        elif self.opt['on_request']:
            packages = []
            for p in full_list:
                installed = self.helper.get_installed(p)
                if installed.get('installed_on_request', True) in [
                    True,
                    None,
                ]:
                    packages.append(p)
        else:
            packages = copy.deepcopy(full_list)

        for p in self.opt['top_packages'].split(','):
            if p == '':
                continue
            if p in full_list and p not in packages:
                packages.append(p)
        return packages

    def get_installed_packages(
        self,
        force_appstore_list: bool = False,
    ) -> None:
        """Get Installed Package List."""
        # Clear lists
        for bi in [*self.brewinfo_ext, self.brewinfo_main]:
            bi.clear_list()

        # Brew packages
        if not self.opt['caskonly']:
            for p in self.get_installed_formulae():
                self.brewinfo.brew_list.append(p)
                self.brewinfo.brew_opt_list[p] = self.helper.get_option(p)

        # Taps
        _, lines = self.helper.proc(
            'brew tap',
            print_cmd=False,
            print_out=False,
        )

        self.brewinfo.set_list_val('tap_list', lines)
        if self.opt['api'] and self.opt[
            'core_repo'
        ] not in self.brewinfo.get_list('tap_list'):
            self.brewinfo.add_to_list('tap_list', [self.opt['core_repo']])
        if (
            is_mac()
            and self.opt['api']
            and self.opt['cask_repo'] not in self.brewinfo.get_list('tap_list')
        ):
            self.brewinfo.add_to_list('tap_list', [self.opt['cask_repo']])

        # Casks
        if is_mac():
            for p in self.helper.get_cask_list():
                if len(p.split()) == 1:
                    self.brewinfo.cask_list.append(p)
                else:
                    self.log.warning(
                        f"The cask file of {p} doesn't exist.",
                    )
                    self.log.warning('Please check later.\n\n')
                    self.brewinfo.cask_nocask_list.append(p)

        # App Store
        if is_mac():
            if self.opt['appstore'] == 1 or (
                self.opt['appstore'] == 2 and force_appstore_list
            ):
                self.brewinfo.set_list_val(
                    'appstore_list',
                    self.get_appstore_list(),
                )
            elif self.opt['appstore'] == 2:
                if self.brewinfo.check_file():
                    self.read_all()
                self.brewinfo.set_list_val(
                    'appstore_list',
                    list(self.get_list('appstore_input')),
                )

        # Whalebrew commands
        if self.opt['whalebrew']:
            self.brewinfo.set_list_val(
                'whalebrew_list',
                self.get_whalebrew_list(),
            )

        # VSCode extensions
        if self.opt['vscode']:
            self.brewinfo.set_list_val('vscode_list', self.get_vscode_list())

        # Cursor extensions
        if self.opt['cursor']:
            self.brewinfo.set_list_val('cursor_list', self.get_cursor_list())
        # Codium extensions
        if self.opt['codium']:
            self.brewinfo.set_list_val('codium_list', self.get_codium_list())

    def clean_list(self) -> None:
        """Remove duplications between brewinfo.list to extra files' input."""
        # Cleanup extra files
        formula_aliases = self.helper.get_formula_aliases(flat=True)
        cask_aliases = self.helper.get_cask_aliases(flat=True)

        # Remove aliases and not installed packages
        for b in [*self.brewinfo_ext, self.brewinfo_main]:
            for line in [
                'brew',
                'tap',
                'cask',
                'appstore',
                'whalebrew',
                'vscode',
                'cursor',
                'codium',
            ]:
                for p in b.get_list(line + '_input'):
                    # Keep aliases
                    if (
                        line == 'brew'
                        and p in formula_aliases
                        and formula_aliases[p]
                        in self.brewinfo.get_list('brew_list')
                    ):
                        self.brewinfo.add_to_list('brew_list', [p])
                        self.brewinfo.add_to_dict(
                            'brew_opt_list',
                            {
                                p: self.brewinfo.get_dict('brew_opt_list')[
                                    formula_aliases[p]
                                ],
                            },
                        )
                        self.brewinfo.remove(
                            'brew_list',
                            formula_aliases[p],
                        )
                        self.brewinfo.remove(
                            'brew_opt_list',
                            formula_aliases[p],
                        )
                    if (
                        line == 'cask'
                        and p in cask_aliases
                        and cask_aliases[p]
                        in self.brewinfo.get_list('cask_list')
                    ):
                        self.brewinfo.add_to_list('cask_list', [p])
                        self.brewinfo.remove('cask_list', cask_aliases[p])

                    if p not in self.brewinfo.get_list(line + '_list'):
                        b.remove(line + '_input', p)

        # Copy list to main file
        self.list_to_main()

        # Loop over lists to remove duplications.
        # tap_list is not checked for overlap removal.
        # Keep it in main list in any case.
        for name in [
            'brew',
            'cask',
            'cask_nocask',
            'appstore',
            'whalebrew',
            'vscode',
            'cursor',
            'codium',
        ]:
            i = 'cask' if name == 'cask_nocask' else name
            for p in self.brewinfo_main.get_list(name + '_list'):
                if p in self.get_list(i + '_input', True):
                    self.brewinfo_main.remove(name + '_list', p)

        # Keep mian/file in main Brewfile
        self.brewinfo_main.add_to_list(
            'main_list',
            self.brewinfo_main.main_input,
        )
        self.brewinfo_main.add_to_list(
            'file_list',
            self.brewinfo_main.file_input,
        )

        # Copy input to list for extra files.
        self.input_to_list(only_ext=True)

    def input_backup(self) -> bool:
        if self.opt['backup'] != '':
            Path(self.opt['input']).rename(Path(self.opt['backup']))
            self.log.info(f'Old input file was moved to {self.opt["backup"]}')
        else:
            ans = self.ask_yn('Do you want to overwrite it?')
            if not ans:
                return False
        return True

    def set_brewfile_local(self) -> None:
        """Set Brewfile to local file."""
        self.opt['repo'] = ''
        _ = self.initialize(check=False, check_input=False)

    def set_brewfile_repo(self) -> bool:
        """Set Brewfile repository."""
        # Check input file
        if self.opt['input'].exists():
            prev_repo = ''
            with Path(self.opt['input']).open() as f:
                lines = f.readlines()
            for line in lines:
                if re.match(' *git ', line) is None:
                    continue
                git_line = line.split()
                if len(git_line) > 1:
                    prev_repo = git_line[1]
                    break
            if self.opt['repo'] == '':
                self.log.info(
                    f'Input file: {self.opt["input"]} is already there.',
                )
                if prev_repo != '':
                    self.log.info(
                        f'git repository for Brewfile is already set as {prev_repo}.',
                    )

            if not self.input_backup():
                return False

        # Get repository
        if self.opt['repo'] == '':
            self.log.info(
                '\nSet repository,\n'
                '"non" (or empty) for local Brewfile '
                f'({self.opt["input"]}),\n'
                '/path/to/repo for local git repository,\n'
                'https://your/git/repository '
                '(or ssh://user@server.project.git) for git repository,\n'
                'or (<user>/)<repo> for github repository,',
            )
            self.opt['repo'] = input('or full path for other git repository: ')
            self.banner('# Set Brewfile repository as ' + self.opt['repo'])

        if self.opt['repo'] in ['non', '']:
            self.set_brewfile_local()
        else:
            # Write repository to the input file
            with OpenWrapper(self.opt['input'], 'w') as f:
                f.write('git ' + self.opt['repo'])
            self.check_repo()
        return True

    def initialize(
        self,
        check: bool = True,
        check_input: bool = True,
        debug_out: bool = False,
    ) -> bool:
        """Initialize Brewfile."""
        if self.opt['initialized']:
            return True

        if check:
            if not self.opt['input'].exists():
                if not self.opt['no_repo']:
                    ans = self.ask_yn(
                        'Do you want to set a repository (y)? '
                        '((n) for local Brewfile).',
                    )
                    if ans and not self.set_brewfile_repo():
                        return False
            elif self.opt['repo'] != '':
                self.log.info(
                    f'You are using Brewfile of {self.opt["repo"]}.',
                )
            else:
                self.log.info(f'{self.opt["input"]} is already there.')
                if not self.input_backup():
                    return False

        # Get installed package list
        self.get_installed_packages()

        # Read inputs
        if check_input:
            if self.brewinfo.check_file():
                self.read_all()

            # Remove duplications between brewinfo.list to extra files' input
            self.clean_list()

        # write out
        self.initialize_write(debug_out=debug_out)

        return True

    def initialize_write(self, debug_out: bool = False) -> None:
        self.write(debug_out=debug_out)
        self.banner(
            f'# You can edit {self.brewinfo.file} with:\n'
            f'#     $ {__prog__} edit',
            debug_out=debug_out,
        )
        self.opt['initialized'] = True

    def check_input_file(self) -> None:
        """Check input file."""
        if not self.brewinfo.check_file():
            self.log.warning(f'Input file {self.brewinfo.file} is not found.')
            ans = self.ask_yn(
                'Do you want to initialize from installed packages?',
            )
            if ans:
                _ = self.initialize(check=False)

            msg = (
                f'Ok, please prepare brewfile\n'
                f'or you can initialize {self.brewinfo.file} with:    $ {__prog__} init'
            )
            raise RuntimeError(msg)

    def get_files(
        self,
        is_print: bool = False,
        all_files: bool = False,
        error_no_file: bool = True,
    ) -> list[Path]:
        """Get Brewfiles."""
        self.read_all()
        files = [
            x.file
            for x in [self.brewinfo_main, *self.brewinfo_ext]
            if all_files or x.file.exists()
        ]
        if error_no_file and not files:
            msg = 'No Brewfile found. Please run `brew file init` first.'
            raise RuntimeError(msg)
        if is_print:
            self.log.info('\n'.join([str(x) for x in files]))
        return files

    def edit_brewfile(self) -> None:
        """Edit brewfiles."""
        editor = shlex.split(self.opt['my_editor'])
        subprocess.call(editor + [str(x) for x in self.get_files()])

    def cat_brewfile(self) -> None:
        """Cat brewfiles."""
        subprocess.call(['cat'] + [str(x) for x in self.get_files()])

    def clean_non_request(self) -> None:
        """Clean up non requested packages."""
        cmd = 'brew autoremove'
        _ = self.helper.proc(
            cmd,
            print_cmd=False,
            print_out=True,
            dryrun=self.opt['dryrun'],
        )

    def cleanup(self, delete_cache: bool = True) -> None:
        """Clean up."""
        # Get installed package list
        self.get_installed_packages()

        # Check up packages in the input file
        self.read_all()

        # Remain formulae in dependencies
        info = self.helper.get_info()['formulae']

        def add_dependncies(package: str) -> None:
            for pac in info[package]['dependencies']:
                p = pac.split('/')[-1]
                if p not in info:
                    continue
                if p not in self.get_list('brew_input'):
                    self.brewinfo.brew_input.append(p)
                    self.brewinfo.brew_opt_input[p] = ''
                    add_dependncies(p)

        for p in self.get_list('brew_input'):
            if p not in info:
                continue
            add_dependncies(p)

        # Clean up Whalebrew images
        if self.opt['whalebrew'] == 1 and self.get_list('whalebrew_list'):
            self.banner('# Clean up Whalebrew images')

            for image in self.get_list('whalebrew_list'):
                if image in self.get_list('whalebrew_input'):
                    continue

                if self.check_whalebrew_cmd(True) == 1:
                    cmd = f'{self.opt["whalebrew_cmd"]} uninstall -y {image.split("/")[-1]}'
                    _ = self.helper.proc(
                        cmd,
                        print_cmd=True,
                        print_out=True,
                        exit_on_err=False,
                        dryrun=self.opt['dryrun'],
                    )
                    self.remove_pack('whalebrew_list', image)

        # Clean up VSCode extensions
        if self.opt['vscode'] == 1 and self.get_list('vscode_list'):
            self.banner('# Clean up VSCode extensions')

            for e in self.get_list('vscode_list'):
                if e in self.get_list('vscode_input'):
                    continue

                if self.check_vscode_cmd(True) == 1:
                    cmd = f'{self.opt["vscode_cmd"]} --uninstall-extension {e}'
                    _ = self.helper.proc(
                        cmd,
                        print_cmd=True,
                        print_out=True,
                        exit_on_err=False,
                        separate_err=True,
                        print_err=False,
                        dryrun=self.opt['dryrun'],
                    )
                    self.remove_pack('vscode_list', e)

        # Clean up Cursor extensions
        if self.opt['cursor'] == 1 and self.get_list('cursor_list'):
            self.banner('# Clean up Cursor extensions')

            for e in self.get_list('cursor_list'):
                if e in self.get_list('cursor_input'):
                    continue

                if self.check_cursor_cmd(True) == 1:
                    cmd = f'{self.opt["cursor_cmd"]} --uninstall-extension {e}'
                    _ = self.helper.proc(
                        cmd,
                        print_cmd=True,
                        print_out=True,
                        exit_on_err=False,
                        separate_err=True,
                        print_err=False,
                        dryrun=self.opt['dryrun'],
                    )
                    self.remove_pack('cursor_list', e)

        # Clean up Codium extensions
        if self.opt['codium'] == 1 and self.get_list('codium_list'):
            self.banner('# Clean up Codium extensions')

            for e in self.get_list('codium_list'):
                if e in self.get_list('codium_input'):
                    continue

                if self.check_codium_cmd(True) == 1:
                    cmd = f'{self.opt["codium_cmd"]} --uninstall-extension {e}'
                    _ = self.helper.proc(
                        cmd,
                        print_cmd=True,
                        print_out=True,
                        exit_on_err=False,
                        separate_err=True,
                        print_err=False,
                        dryrun=self.opt['dryrun'],
                    )
                    self.remove_pack('codium_list', e)

        # Clean up App Store applications
        if self.opt['appstore'] == 1 and self.get_list('appstore_list'):
            self.banner('# Clean up App Store applications')

            for p in self.get_list('appstore_list'):
                identifier = p.split()[0]
                if identifier.isdigit():
                    package = ' '.join(p.split()[1:])
                else:
                    identifier = ''
                    package = p
                if re.match(r'.*\(\d+\.\d+.*\)$', package):
                    package = ' '.join(package.split(' ')[:-1])

                isinput = False
                for pi in self.get_list('appstore_input'):
                    i_identifier = pi.split()[0]
                    if i_identifier.isdigit():
                        i_package = ' '.join(pi.split()[1:])
                    else:
                        i_identifier = ''
                        i_package = pi
                    if re.match(r'.*\(\d+\.\d+.*\)$', i_package):
                        i_package = ' '.join(i_package.split(' ')[:-1])
                    if (
                        identifier != '' and identifier == i_identifier
                    ) or package == i_package:
                        isinput = True
                        break
                if isinput:
                    continue

                if identifier and self.check_mas_cmd(True) == 1:
                    cmd = (
                        'sudo '
                        + self.opt['mas_cmd']
                        + ' uninstall '
                        + identifier
                    )
                else:
                    ret, _ = self.helper.proc(
                        'type uninstall',
                        print_cmd=False,
                        print_out=False,
                        exit_on_err=False,
                    )
                    cmd = 'sudo uninstall' if ret == 0 else 'sudo rm -rf'
                    tmpcmd = cmd
                    for d in self.opt['appdirlist']:
                        a = f'{d}/{package}.app'
                        if Path(a).is_dir():
                            if ret == 0:
                                cmd += ' file://' + quote(a)
                            else:
                                cmd += f" '{a}'"
                            continue
                    if cmd == tmpcmd:
                        self.log.warning(
                            f'Package {package} was not found:'
                            'nothing to do.\n',
                        )
                        self.remove_pack('appstore_list', p)
                        continue
                _ = self.helper.proc(
                    cmd,
                    print_cmd=True,
                    print_out=True,
                    exit_on_err=False,
                    dryrun=self.opt['dryrun'],
                )
                self.remove_pack('appstore_list', p)

        # Clean up cask packages
        if is_mac() and self.get_list('cask_list'):
            self.banner('# Clean up cask packages')
            non_alias_cask_input = self.get_non_alias_input('casks')
            uninstalls = []
            for p in self.get_list('cask_list'):
                if p in non_alias_cask_input:
                    continue
                uninstalls.append(p)
                self.remove_pack('cask_list', p)

            if uninstalls:
                cmd = 'brew uninstall ' + shlex.join(uninstalls)
                _ = self.helper.proc(
                    cmd,
                    print_cmd=True,
                    print_out=True,
                    dryrun=self.opt['dryrun'],
                )

        # Clean up brew packages
        if self.get_list('brew_list'):
            self.banner('# Clean up brew packages')
            non_alias_brew_input = self.get_non_alias_input('formulae')
            uninstalls = []
            for p in self.get_list('brew_list'):
                if p in non_alias_brew_input:
                    continue
                uninstalls.append(p)
                # Use --ignore-dependencies option to remove packages w/o
                # formula (tap of which could be removed before).
            if uninstalls:
                cmd = 'brew uninstall --ignore-dependencies ' + shlex.join(
                    uninstalls
                )
                _ = self.helper.proc(
                    cmd,
                    print_cmd=False,
                    print_out=True,
                    dryrun=self.opt['dryrun'],
                )

        # Clean up tap packages
        if self.get_list('tap_list'):
            self.banner('# Clean up tap packages')
            untaps = []
            for p in self.get_list('tap_list'):
                # Skip core and cask taps
                if p in [self.opt['core_repo'], self.opt['cask_repo']]:
                    continue
                if p in self.get_list('tap_input'):
                    continue
                tap_packs = self.helper.get_tap_packs(p, alias=True)
                untapflag = True
                for tp in tap_packs['formulae']:
                    if tp in self.get_list('brew_input'):
                        # Keep the Tap as related package is remained
                        untapflag = False
                        break
                if not untapflag:
                    continue
                if is_mac():
                    for tc in tap_packs['casks']:
                        if tc in self.get_list('cask_input'):
                            # Keep the Tap as related cask is remained
                            untapflag = False
                            break
                if not untapflag:
                    continue
                untaps.append(p)

            if untaps:
                cmd = 'brew untap ' + shlex.join(untaps)
                _ = self.helper.proc(
                    cmd,
                    print_cmd=True,
                    print_out=True,
                    dryrun=self.opt['dryrun'],
                )

        # Clean up cashe
        self.banner('# Clean up cache')
        cmd0 = 'brew cleanup'
        _ = self.helper.proc(
            cmd0,
            print_cmd=True,
            print_out=True,
            dryrun=self.opt['dryrun'],
        )
        if delete_cache:
            cmd1 = 'rm -rf ' + self.helper.brew_val('cache')
            _ = self.helper.proc(
                cmd1,
                print_cmd=True,
                print_out=True,
                dryrun=self.opt['dryrun'],
            )

    def install(self) -> None:
        # Get installed package list
        self.get_installed_packages(force_appstore_list=True)

        # Check packages in the input file
        self.read_all()

        # before commands
        for c in self.get_list('before_input'):
            _ = self.helper.proc(c, dryrun=self.opt['dryrun'])

        # Tap
        for p in self.get_list('tap_input'):
            if p in self.get_list('tap_list'):
                continue
            _ = self.helper.proc('brew tap ' + p, dryrun=self.opt['dryrun'])

        # Cask
        if is_mac():
            cask_args_opt = {'--cask': '', '--force': ''}
            cask_args_opt.update(self.get_dict('cask_args_input'))

            cask_aliases = self.helper.get_cask_aliases(flat=True)
            casks_to_install: list[str] = []

            for p in self.get_list('cask_input'):
                pack = cask_aliases.get(p, p)
                if pack in self.get_list('cask_list'):
                    continue
                casks_to_install.append(p)

            if casks_to_install:
                args: list[str] = []
                for k, v in cask_args_opt.items():
                    args.append(k)
                    if v != '':
                        args.append(v)
                cmd = 'brew install ' + shlex.join(args + casks_to_install)
                _ = self.helper.proc(cmd, dryrun=self.opt['dryrun'])

        # Brew
        if not self.opt['caskonly']:
            formula_aliases = self.helper.get_formula_aliases(flat=True)
            batched_packages: list[str] = []
            individual_installs: list[tuple[str, str]] = []

            def handle_install_output(lines: list[str]) -> None:
                for line in lines:
                    if line.find('ln -s') != -1 and self.opt['link']:
                        cmdtmp = line.split()
                        cmd_ln = [str(expandpath(c)) for c in cmdtmp]
                        _ = self.helper.proc(cmd_ln)
                    if line.find('brew linkapps') != -1 and self.opt['link']:
                        _ = self.helper.proc('brew linkapps')

            for p in self.get_list('brew_input'):
                pack = formula_aliases.get(p, p)
                opts = self.get_dict('brew_opt_input')[p]
                if pack in self.get_list('brew_full_list'):
                    if p not in self.get_dict('brew_opt_list') or sorted(
                        opts.split(),
                    ) == sorted(self.get_dict('brew_opt_list')[p].split()):
                        continue
                    # Uninstall to install the package with new options
                    # `reinstall` does not accept options such a --HEAD.
                    _ = self.helper.proc(
                        'brew uninstall ' + p,
                        dryrun=self.opt['dryrun'],
                    )
                if opts.strip():
                    individual_installs.append((p, opts))
                else:
                    batched_packages.append(p)

            if batched_packages:
                ret, lines = self.helper.proc(
                    'brew install ' + shlex.join(batched_packages),
                    dryrun=self.opt['dryrun'],
                )
                if ret != 0:
                    self.log.warning(
                        f'Failed to install packages: {", ".join(batched_packages)}. Please check the package names.'
                    )
                else:
                    handle_install_output(lines)

            for p, opts in individual_installs:
                ret, lines = self.helper.proc(
                    'brew install ' + p + opts,
                    dryrun=self.opt['dryrun'],
                )
                if ret != 0:
                    self.log.warning(
                        f'Can not install {p} .'
                        'Please check the package name.\n'
                        f'{p} may be installed '
                        'by using web direct formula.',
                    )
                    continue
                handle_install_output(lines)

        # App Store
        if is_mac() and self.opt['appstore']:
            id_list = [x.split()[0] for x in self.get_list('appstore_list')]
            for p in self.get_list('appstore_input'):
                identifier = p.split()[0]
                if identifier in id_list:
                    continue
                if identifier.isdigit() and len(identifier) >= 9:
                    package = ' '.join(p.split()[1:])
                else:
                    identifier = ''
                    package = p
                islist = False
                for pl in self.get_list('appstore_list'):
                    l_identifier = pl.split()[0]
                    if l_identifier.isdigit() and len(l_identifier) >= 9:
                        l_package = ' '.join(pl.split()[1:])
                    else:
                        l_identifier = ''
                        l_package = pl
                    if package == l_package:
                        islist = True
                        break
                if islist:
                    continue
                self.log.info(f'Installing {package}')
                if identifier != '':
                    if self.opt['dryrun'] or self.check_mas_cmd(True) == 1:
                        _ = self.helper.proc(
                            self.opt['mas_cmd'] + ' install ' + identifier,
                            dryrun=self.opt['dryrun'],
                        )
                    else:
                        self.log.info(
                            f'Please install {package} from AppStore.',
                        )
                        _ = self.helper.proc(
                            f"open -W 'macappstore://itunes.apple.com/app/id{identifier}'",
                            dryrun=self.opt['dryrun'],
                        )
                else:
                    self.log.warning(
                        'No id or wrong id information was given for '
                        f'AppStore App: {package}.\n'
                        'Please install it manually.',
                    )

        # Whalebrew commands
        if self.opt['whalebrew']:
            images = self.get_list('whalebrew_list')
            for image in self.get_list('whalebrew_input'):
                if image in images:
                    continue
                self.log.info(f'Installing {image}')
                if self.opt['dryrun'] or self.check_whalebrew_cmd(True) == 1:
                    if not self.opt[
                        'dryrun'
                    ] and self.check_docker_running() in [-1, -2]:
                        if self.check_docker_running() == -1:
                            self.log.warning(
                                'Docker command is not available.',
                            )
                        elif self.check_docker_running() == -2:
                            self.log.warning('Docker is not running.')
                        self.log.warning(
                            f'Please install {image} by whalebrew after docker is ready.',
                        )
                        continue
                    _ = self.helper.proc(
                        self.opt['whalebrew_cmd'] + ' install ' + image,
                        dryrun=self.opt['dryrun'],
                    )
                else:
                    self.log.warning(f'Please install {image} by whalebrew.')

        # VSCode extensions
        if self.opt['vscode']:
            extensions = self.get_list('vscode_list')
            for e in self.get_list('vscode_input'):
                if e in extensions:
                    continue
                self.log.info(f'Installing {e}')
                if self.opt['dryrun'] or self.check_vscode_cmd(True) == 1:
                    _ = self.helper.proc(
                        self.opt['vscode_cmd'] + ' --install-extension ' + e,
                        separate_err=True,
                        print_err=False,
                        dryrun=self.opt['dryrun'],
                    )
                else:
                    self.log.warning(f'Please install {e} to VSCode.')

        # Cursor extensions
        if self.opt['cursor']:
            extensions = self.get_list('cursor_list')
            for e in self.get_list('cursor_input'):
                if e in extensions:
                    continue
                self.log.info(f'Installing {e}')
                if self.opt['dryrun'] or self.check_cursor_cmd(True) == 1:
                    _ = self.helper.proc(
                        self.opt['cursor_cmd'] + ' --install-extension ' + e,
                        separate_err=True,
                        print_err=False,
                        dryrun=self.opt['dryrun'],
                    )
                else:
                    self.log.warning(f'Please install {e} to Cursor.')

        # Codium extensions
        if self.opt['codium']:
            extensions = self.get_list('codium_list')
            for e in self.get_list('codium_input'):
                if e in extensions:
                    continue
                self.log.info(f'Installing {e}')
                if self.opt['dryrun'] or self.check_codium_cmd(True) == 1:
                    _ = self.helper.proc(
                        self.opt['codium_cmd'] + ' --install-extension ' + e,
                        separate_err=True,
                        print_err=False,
                        dryrun=self.opt['dryrun'],
                    )
                else:
                    self.log.warning(f'Please install {e} to Codium.')

        # Other commands
        for c in self.get_list('cmd_input'):
            _ = self.helper.proc(c, dryrun=self.opt['dryrun'])

        # after commands
        for c in self.get_list('after_input'):
            _ = self.helper.proc(c, dryrun=self.opt['dryrun'])

    def generate_cask_token(self, app: str) -> str:
        # Ref: https://github.com/Homebrew/homebrew-cask/blob/c24db49e9489190949096156a1f97ee02c15c68b/developer/bin/generate_cask_token#L267
        token = app.split('/')[-1]
        token = token.removesuffix('.app')
        token = token.replace('+', 'plus')
        token = token.replace('@', 'at')
        token = token.replace(' ', '-').lower()
        token = re.sub(r'[^a-z0-9-]', '', token)
        token = re.sub(r'-+', '-', token)
        token = re.sub(r'^-+', '', token)
        return re.sub(r'-([0-9])', '\\g<1>', token)

    def make_brew_app_cmd(self, name: str, app_path: str) -> str:
        return f'brew {name} # {app_path}'

    def make_cask_app_cmd(self, name: str, app_path: str) -> str:
        return f'cask {name} # {app_path}'

    def make_appstore_app_cmd(self, name: str, app_path: str) -> str:
        return f'appstore {name} # {app_path}'

    def check_cask(self) -> None:
        """Check applications for Cask."""
        if not is_mac():
            msg = 'Cask is not available on Linux!'
            raise RuntimeError(msg)

        self.banner('# Starting to check applications for Cask...')

        # First, get App Store applications
        appstore_list = self.get_appstore_dict()

        # Get all available formulae/casks information
        all_info = self.helper.get_all_info()

        casks: dict[str, dict[str, str | bool]] = {}
        apps: dict[str, str] = {}
        installed_casks: dict[str, list[str]] = {self.opt['cask_repo']: []}
        for cask, info in all_info['casks'].items():
            installed = False
            latest = False
            if info.get('installed'):
                installed = True
                latest = info['installed'] == info['version']
                installed_casks[info['tap']] = [
                    *(
                        installed_casks.get(
                            info['tap'],
                            [],
                        )
                    ),
                    cask,
                ]

            apps_in_cask: list[str] = []
            if 'artifacts' in info:
                for artifact in info['artifacts']:
                    if 'app' in artifact:
                        apps_in_cask = apps_in_cask + [
                            a for a in artifact['app'] if isinstance(a, str)
                        ]
                    if 'uninstall' in artifact:
                        for uninstall in artifact['uninstall']:
                            if 'delete' in uninstall:
                                apps_in_cask = apps_in_cask + [
                                    a
                                    for a in uninstall['delete']
                                    if isinstance(a, str)
                                ]
            casks[cask] = {
                'tap': info['tap'],
                'installed': installed,
                'latest': latest,
            }
            apps_in_cask = list(set(apps_in_cask))
            for a in apps_in_cask:
                if a not in apps or installed:
                    apps[a] = cask

        # Set applications directories
        app_dirs = self.opt['appdirlist']
        apps_check = {
            'cask': dict.fromkeys(app_dirs, 0),
            'has_cask': dict.fromkeys(app_dirs, 0),
            'brew': dict.fromkeys(app_dirs, 0),
            'has_brew': dict.fromkeys(app_dirs, 0),
            'appstore': dict.fromkeys(app_dirs, 0),
            'no_cask': dict.fromkeys(app_dirs, 0),
        }

        appstore_apps: dict[str, str] = {}
        appstore_has_cask_apps: CaskInfo = {}
        cask_apps: CaskListInfo = {self.opt['cask_repo']: []}
        non_latest_cask_apps: CaskListInfo = {self.opt['cask_repo']: []}
        has_cask_apps: CaskListInfo = {self.opt['cask_repo']: []}
        brew_apps: CaskListInfo = {self.opt['core_repo']: []}
        has_brew_apps: CaskListInfo = {self.opt['core_repo']: []}
        no_cask: list[str] = []

        # Get applications
        napps = 0
        for d in app_dirs:
            for app in sorted(
                [
                    str(a)
                    for a in Path(d).iterdir()
                    if not str(a).startswith('.')
                    and str(a) != 'Utilities'
                    and (Path(d) / a).is_dir()
                ],
            ):
                check = 'no_cask'
                app_path = home_tilde(f'{d}/{app}')
                aname = app
                aname = aname.removesuffix('.app')
                if app in apps:
                    token = apps[app]
                elif app_path in apps:
                    token = apps[app_path]
                else:
                    token = self.generate_cask_token(app)

                if aname in appstore_list:
                    check = 'appstore'
                    name = (
                        appstore_list[aname][0]
                        + ' '
                        + aname
                        + ' '
                        + appstore_list[aname][1]
                    )
                    if token in casks:
                        appstore_has_cask_apps[name] = (token, app_path)
                    else:
                        appstore_apps[name] = app_path
                elif token in casks:
                    cask_tap = cast('str', casks[token]['tap'])
                    if casks[token]['installed']:
                        check = 'cask'
                        if casks[token]['latest']:
                            cask_apps[cask_tap] = [
                                *(
                                    cask_apps.get(
                                        cask_tap,
                                        [],
                                    )
                                ),
                                (app_path, token),
                            ]
                        else:
                            non_latest_cask_apps[cask_tap] = [
                                *(non_latest_cask_apps.get(cask_tap, [])),
                                (app_path, token),
                            ]
                        if token in installed_casks[cask_tap]:
                            installed_casks[cask_tap].remove(token)
                    else:
                        check = 'has_cask'
                        has_cask_apps[cask_tap] = [
                            *(
                                has_cask_apps.get(
                                    cask_tap,
                                    [],
                                )
                            ),
                            (app_path, token),
                        ]
                elif token in all_info['formulae']:
                    brew_tap = cast(
                        'str',
                        all_info['formulae'][token]['tap'],
                    )
                    if all_info['formulae'][token]['installed']:
                        check = 'brew'
                        brew_apps[brew_tap] = [
                            *(
                                brew_apps.get(
                                    brew_tap,
                                    [],
                                )
                            ),
                            (app_path, token),
                        ]
                    else:
                        check = 'has_brew'
                        has_brew_apps[brew_tap] = [
                            *(
                                has_brew_apps.get(
                                    brew_tap,
                                    [],
                                )
                            ),
                            (app_path, token),
                        ]
                if check == 'no_cask':
                    no_cask.append(app_path)
                apps_check[check][d] += 1
                napps += 1

        # Make list
        casks_in_others = []
        output = ''

        output += '# Cask applications\n\n'

        for tap in set(cask_apps.keys()) or set(has_cask_apps.keys()):
            output += f'# Apps installed by cask in {tap}\n'
            if tap != self.opt['cask_repo'] or not self.opt['api']:
                output += f'tap {tap}\n'
            for app_path, token in sorted(cask_apps[tap], key=lambda x: x[1]):
                if token not in casks_in_others:
                    output += self.make_cask_app_cmd(token, app_path) + '\n'
                    casks_in_others.append(token)
                else:
                    output += f'#{self.make_cask_app_cmd(token, app_path)}\n'
            output += '\n'

            if non_latest_cask_apps.get(tap):
                output += '# New version are available for following apps\n'
                for app_path, token in sorted(non_latest_cask_apps[tap]):
                    if token not in casks_in_others:
                        output += (
                            self.make_cask_app_cmd(token, app_path) + '\n'
                        )
                        casks_in_others.append(token)
                    else:
                        output += (
                            f'#{self.make_cask_app_cmd(token, app_path)}\n'
                        )
                output += '\n'

            if installed_casks.get(tap):
                output += '# Cask is found, but no applications are found (could be fonts, system settings, or installed in other directory.)\n'
                for token in sorted(installed_casks[tap]):
                    if token not in casks_in_others:
                        output += f'cask {token}\n'
                        casks_in_others.append(token)
                    else:
                        output += f'#cask {token}\n'
                output += '\n'

            if has_cask_apps.get(tap):
                output += '# Apps installed directly instead of by cask\n'
                for app_path, token in sorted(has_cask_apps[tap]):
                    output += f'#{self.make_cask_app_cmd(token, app_path)}\n'
                output += '\n'

        for tap in set(brew_apps.keys()) or set(has_brew_apps.keys()):
            output += f'# Apps installed by brew in {tap}\n'
            if tap != self.opt['core_repo'] or not self.opt['api']:
                output += f'tap {tap}\n'
            for app_path, token in sorted(brew_apps[tap], key=lambda x: x[1]):
                if token not in casks_in_others:
                    output += self.make_brew_app_cmd(token, app_path) + '\n'
                    casks_in_others.append(token)
                else:
                    output += f'#{self.make_brew_app_cmd(token, app_path)}\n'
            output += '\n'

            if has_brew_apps.get(tap):
                output += '# Apps installed directly instead of by brew\n'
                for app_path, token in sorted(has_brew_apps[tap]):
                    output += f'#{self.make_brew_app_cmd(token, app_path)}\n'
                output += '\n'

        if appstore_apps:
            output += '# Apps installed from AppStore\n'
            for name, app_path in appstore_apps.items():
                output += self.make_appstore_app_cmd(name, app_path) + '\n'
            output += '\n'

        if appstore_has_cask_apps:
            output += (
                '# Apps installed from AppStore, but casks are available.\n'
            )
            for name, (token, app_path) in appstore_has_cask_apps.items():
                output += (
                    self.make_appstore_app_cmd(name, f'{token}, {app_path}')
                    + '\n'
                )
            output += '\n'

        if no_cask:
            output += '# Apps installed but no casks are available\n'
            output += '# (System applications or directory installed.)\n'
            for app_path in no_cask:
                output += f'# {app_path}\n'

        with Path('Caskfile').open('w') as f:
            f.write(output)
        self.log.debug(output)

        # Summary
        self.banner('# Summary')
        self.log.info(
            f'Total:{napps} apps have been checked.\n'
            f'Apps in {[home_tilde(d) for d in app_dirs]}\n',
        )
        maxlen = max(len(home_tilde(x)) for x in app_dirs)
        if sum(apps_check['cask'].values()) > 0:
            self.log.info('Installed by Cask:')
            for d in app_dirs:
                if apps_check['cask'][d] == 0:
                    continue
                self.log.info(
                    f'{home_tilde(d):{maxlen}s} : {apps_check["cask"][d]}',
                )
            self.log.info('')
        if sum(apps_check['brew'].values()) > 0:
            self.log.info('Installed by brew install command')
            for d in app_dirs:
                if apps_check['brew'][d] == 0:
                    continue
                self.log.info(
                    f'{home_tilde(d):{maxlen}s} : {apps_check["brew"][d]}',
                )
            self.log.info('')
        if sum(apps_check['has_cask'].values()) > 0:
            self.log.info('Installed directly, but casks are available:')
            for d in app_dirs:
                if apps_check['has_cask'][d] == 0:
                    continue
                self.log.info(
                    f'{home_tilde(d):{maxlen}s} : {apps_check["has_cask"][d]}',
                )
            self.log.info('')
        if sum(apps_check['appstore'].values()) > 0:
            self.log.info('Installed from Appstore')
            for d in app_dirs:
                if apps_check['appstore'][d] == 0:
                    continue
                self.log.info(
                    f'{home_tilde(d):{maxlen}s} : {apps_check["appstore"][d]}',
                )
            self.log.info('')
        if sum(apps_check['no_cask'].values()) > 0:
            self.log.info('No casks')
            for d in app_dirs:
                if apps_check['no_cask'][d] == 0:
                    continue
                self.log.info(
                    f'{home_tilde(d):{maxlen}s} : {apps_check["no_cask"][d]}',
                )
            self.log.info('')

    def execute(self) -> None:
        """Execute."""
        # Cask list check
        if self.opt['command'] == 'casklist':
            self.check_cask()
            return

        # Set BREWFILE repository
        if self.opt['command'] == 'set_repo':
            _ = self.set_brewfile_repo()
            return

        # Set BREWFILE to local file
        if self.opt['command'] == 'set_local':
            self.set_brewfile_local()
            return

        # Change brewfile if it is repository's one or not.
        self.check_repo()

        # Do pull/push for the repository.
        if self.opt['command'] in ['pull', 'push']:
            with self.DryrunBanner(self):
                self.repomgr(self.opt['command'])
            return

        # brew command
        if self.opt['command'] == 'brew':
            with self.DryrunBanner(self):
                self.brew_cmd()
            return

        # Initialize
        if self.opt['command'] in ['init', 'dump']:
            _ = self.initialize()
            return

        # Edit
        if self.opt['command'] == 'edit':
            self.edit_brewfile()
            return

        # Cat
        if self.opt['command'] == 'cat':
            self.cat_brewfile()
            return

        # Get files
        if self.opt['command'] == 'get_files':
            self.get_files(is_print=True, all_files=self.opt['all_files'])
            return

        # Check input file
        # If the file doesn't exist, initialize it.
        self.check_input_file()

        # Cleanup non request
        if self.opt['command'] == 'clean_non_request':
            with self.DryrunBanner(self):
                self.clean_non_request()
            return

        # Cleanup
        if self.opt['command'] == 'clean':
            with self.DryrunBanner(self):
                self.cleanup()
            return

        # Install
        if self.opt['command'] == 'install':
            with self.DryrunBanner(self):
                self.install()
            return

        # Update
        if self.opt['command'] == 'update':
            with self.DryrunBanner(self):
                if not self.opt['noupgradeatupdate']:
                    _ = self.helper.proc(
                        'brew update',
                        dryrun=self.opt['dryrun'],
                    )
                    fetch_head = (
                        '--fetch-HEAD' if self.opt['fetch_head'] else ''
                    )
                    _ = self.helper.proc(
                        f'brew upgrade --formula {fetch_head}',
                        dryrun=self.opt['dryrun'],
                    )
                    if is_mac():
                        _ = self.helper.proc(
                            'brew upgrade --cask',
                            dryrun=self.opt['dryrun'],
                        )
                if self.opt['repo'] != '':
                    self.repomgr('pull')
                self.install()
                self.cleanup(delete_cache=False)
                if not self.opt['dryrun']:
                    _ = self.initialize(check=False, debug_out=True)
                if self.opt['repo'] != '':
                    self.repomgr('push')
            return

        # No command found
        msg = (
            f'Wrong command: {self.opt["command"]}\n'
            f'Execute `{__prog__} help` for more information.'
        )
        raise RuntimeError(msg)
