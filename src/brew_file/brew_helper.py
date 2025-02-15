from __future__ import annotations

import json
import logging
import os
import shlex
import subprocess
from collections.abc import Generator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypedDict, cast


class ProcParams(TypedDict):
    """Parameters for BrewHelper.proc()."""

    cmd: str | list[str]
    print_cmd: bool
    print_out: bool
    exit_on_err: bool
    separate_err: bool
    print_err: bool
    env: dict[str, str] | None
    cwd: str | Path | None
    dryrun: bool


class CmdError(Exception):
    """Exception at command execution."""

    def __init__(self, message: str, return_code: int) -> None:
        super().__init__(message)
        self.return_code = return_code


@dataclass
class BrewHelper:
    """Helper functions for BrewFile."""

    opt: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.log = logging.getLogger(__name__)

        self.all_info: dict[str, dict[str, Any]] = {}
        self.info: dict[str, dict[str, Any]] = {}

        self.packages: dict[str, list[str]] = {}

        self.aliases: dict[str, dict[str, dict[str, str]]] = {}
        self.taps: dict[str, Any] | None = None
        self.leaves_list: list[str] | None = None
        self.leaves_list_on_request: list[str] | None = None

    def readstdout(
        self,
        proc: subprocess.Popen[str],
    ) -> Generator[str, None, None]:
        if proc.stdout is None:
            return
        for out_line in iter(proc.stdout.readline, ''):
            line = out_line.rstrip()
            if line == '':
                continue
            yield line

    def proc(
        self,
        cmd: str | list[str],
        print_cmd: bool = True,
        print_out: bool = True,
        exit_on_err: bool = True,
        separate_err: bool = False,
        print_err: bool = True,
        env: dict[str, str] | None = None,
        cwd: str | Path | None = None,
        dryrun: bool = False,
    ) -> tuple[int, list[str]]:
        """Get process output."""
        if env is None:
            env = {}
        if not isinstance(cmd, list):
            cmd = shlex.split(cmd)
        cmd_orig = ' '.join(['$', *cmd])
        if cmd[0] == 'brew':
            cmd[0] = self.opt.get('brew_cmd', 'brew')
        if print_cmd or dryrun:
            self.log.info(cmd_orig)
        if dryrun:
            return 0, [' '.join(cmd)]
        all_env = os.environ.copy()
        all_env.update(env)
        lines = []
        try:
            if separate_err:
                stderr = None if print_err else subprocess.PIPE
            else:
                stderr = subprocess.STDOUT
            p = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=stderr,
                text=True,
                env=all_env,
                cwd=cwd,
            )
            for line in self.readstdout(p):
                lines.append(line)
                if print_out:
                    self.log.info(line)
            ret = p.wait()
        except OSError as e:
            if separate_err:
                if print_err:
                    self.log.error(str(e))  # noqa: TRY400
            else:
                lines += str(e).splitlines()
                if print_out:
                    self.log.info(str(e))
            ret = e.errno if e.errno is not None else 1

        if exit_on_err and ret != 0:
            output = '\n'.join(lines)
            msg = f'Failed at command: {" ".join(cmd)}\n{output}'
            raise CmdError(msg, ret)
        return ret, lines

    def brew_val(self, name: str) -> str:
        if name not in self.opt:
            _, lines = self.proc('brew --' + name, False, False)
            self.opt[name] = lines[0]
        return self.opt[name]

    def name_key(self) -> str:
        return 'full_name' if self.opt['full_name'] else 'name'

    def token_key(self) -> str:
        return 'full_token' if self.opt['full_name'] else 'token'

    def get_packages(self, package_type: str) -> list[str]:
        if (packages := self.packages.get(package_type, None)) is not None:
            return packages
        _, lines = self.proc(
            cmd=f'brew {package_type}',
            print_cmd=False,
            print_out=False,
            exit_on_err=True,
            separate_err=True,
        )
        # Test formulae in a deep directory was found in hashicorp/tap
        # Allow only short name and tap + name
        packages = [x for x in lines if len(x.split('/')) in (1, 3)]
        self.packages[package_type] = packages
        return packages

    def get_formulae(self) -> list[str]:
        return self.get_packages('formulae')

    def get_casks(self) -> list[str]:
        return self.get_packages('casks')

    def get_json_info(
        self, args: str, exit_on_err: bool
    ) -> dict[str, Any] | list[str]:
        ret, lines = self.proc(
            cmd=f'brew info --json=v2 {args}',
            print_cmd=False,
            print_out=False,
            exit_on_err=exit_on_err,
            separate_err=False,
        )
        if ret != 0:
            return lines
        lines = lines[lines.index('{') :]
        data = json.loads(''.join(lines[lines.index('{') :]))
        return {
            'formulae': {
                x[self.name_key()]: x for x in data.get('formulae', [])
            },
            'casks': {x[self.token_key()]: x for x in data.get('casks', [])},
        }

    def get_each_type_info(self, package_type: str) -> dict[str, Any]:
        packages = self.get_packages(package_type)
        while True:
            info = self.get_json_info(
                f'--{package_type} {" ".join(packages)}',
                False,
            )

            if isinstance(info, dict):
                return info[package_type]

            updated = 0
            for line in info:
                package = ''
                if 'requires at least a URL' in line:
                    # Remove package from list if it has no URL
                    # https://github.com/hashicorp/homebrew-tap/issues/258
                    package = line.split()[1].strip(':')
                elif 'No available' in line:
                    # Remove non-package
                    # This can be found in hashicorp/tap
                    # ("util" directory is misunderstood as a package)
                    package = line.split('with the name ')[1].strip('".')
                if package:
                    if package in packages:
                        packages.remove(package)
                        updated = 1
                    if (short_name := package.split('/')[-1]) in packages:
                        packages.remove(short_name)
                        updated = 1
            if updated:
                continue
            msg = f'Failed to get info of all {package_type}.\n\n'
            msg += '\n'.join(info)
            raise RuntimeError(msg)

    def get_all_info(self) -> dict[str, dict[str, Any]]:
        """Get info of all available brew package."""
        if 'formulae' in self.all_info and 'casks' in self.all_info:
            return self.all_info

        info = self.get_json_info('--eval-all', False)
        if isinstance(info, dict):
            self.all_info = info
            return self.all_info

        self.all_info = {
            'formulae': self.get_each_type_info('formulae'),
            'casks': self.get_each_type_info('casks'),
        }
        return self.all_info

    def get_info(self) -> dict[str, Any]:
        """Get info of installed brew package."""
        if 'formulae' in self.info and 'casks' in self.info:
            return self.info

        self.info = cast(
            dict[str, Any], self.get_json_info('--installed', True)
        )
        return self.info

    def get_formula_list(self) -> list[str]:
        info = self.get_info()
        return list(info['formulae'].keys())

    def get_cask_list(self) -> list[str]:
        info = self.get_info()
        return list(info['casks'].keys())

    def get_aliases(self, package_type: str) -> dict[str, dict[str, str]]:
        if package_type in self.aliases:
            return self.aliases[package_type]

        self.aliases = {package_type: {}}
        info = self.get_info()
        oldnames = 'oldnames' if package_type == 'formulae' else 'old_tokens'
        key = (
            self.name_key() if package_type == 'formulae' else self.token_key()
        )
        for package in info[package_type].values():
            tap = package['tap']
            for o in package.get(oldnames, []):
                self.aliases[package_type][tap] = self.aliases[
                    package_type
                ].get(tap, {})
                self.aliases[package_type][tap][o] = package[key]
            for a in package.get('aliases', []):
                self.aliases[package_type][tap] = self.aliases[
                    package_type
                ].get(tap, {})
                self.aliases[package_type][tap][a] = package[key]
        return self.aliases[package_type]

    def get_formula_aliases(self) -> dict[str, dict[str, str]]:
        return self.get_aliases('formulae')

    def get_cask_aliases(self) -> dict[str, dict[str, str]]:
        return self.get_aliases('casks')

    def get_installed(self, package: str) -> dict[str, Any]:
        """Get installed version of brew package."""
        installed = {}
        package_info = self.get_info()['formulae'][package]

        if (version := package_info['linked_keg']) is None:
            version = package_info['installed'][-1]['version']

        if version != '':
            for i in package_info['installed']:
                if i['version'].replace('.reinstall', '') == version:
                    installed = i
                    break
        return installed

    def get_option(self, package: str) -> str:
        """Get install options from brew info."""
        opt = ''
        if used_options := self.get_installed(package).get('used_options', []):
            opt = ' ' + ' '.join(used_options)
        if version := self.get_installed(package).get('version', None):
            info = self.get_info()['formulae'][package]

            for k, v in info.get('versions', {}).items():
                if version == v and k != 'stable':
                    if k == 'head':
                        opt += ' --HEAD'
                    else:
                        opt += ' --' + k
        return opt

    def get_tap_packs(
        self,
        tap: str,
        alias: bool = False,
    ) -> dict[str, list[str]]:
        if self.taps is None:
            _, lines = self.proc(
                cmd='brew tap-info --json --installed',
                print_cmd=False,
                print_out=False,
                exit_on_err=True,
                separate_err=True,
            )
            lines = lines[lines.index('[') :]
            data = json.loads(''.join(lines))
            self.taps = {x['name']: x for x in data}

        packs = {
            'formulae': self.taps[tap]['formula_names'],
            'casks': self.taps[tap]['cask_tokens'],
        }
        if not self.opt['full_name']:
            packs = {
                'formulae': [x.split('/')[-1] for x in packs['formulae']],
                'casks': [x.split('/')[-1] for x in packs['casks']],
            }

        if alias:
            packs['formulae'] += list(
                self.get_formula_aliases().get(tap, {}).keys(),
            )
            packs['casks'] += list(self.get_cask_aliases().get(tap, {}).keys())
        return packs

    def get_leaves(self, on_request: bool = False) -> list[str]:
        if on_request:
            leaves_list = self.leaves_list_on_request
        else:
            leaves_list = self.leaves_list

        if leaves_list is not None:
            return leaves_list

        cmd = 'brew leaves'
        if on_request:
            cmd += ' --installed-on-request'
        _, lines = self.proc(
            cmd,
            print_cmd=False,
            print_out=False,
            separate_err=True,
            print_err=False,
        )
        leaves_list = [x.split('/')[-1] for x in lines]
        if on_request:
            self.leaves_list_on_request = leaves_list
        else:
            self.leaves_list = leaves_list
        return leaves_list

    def get_full_name(self, package: str) -> str:
        """Get full name (user/tap/package) of a package."""
        info = self.get_info()
        tap = ''
        if package in info['formulae']:
            tap = info['formulae'][package]['tap']
        elif package in info['casks']:
            tap = info['casks'][package]['tap']
        if not tap or tap in [self.opt['core_repo'], self.opt['cask_repo']]:
            return package
        return f'{tap}/{package}'
