from __future__ import annotations

import json
import logging
import os
import shlex
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Generator, TypedDict

if TYPE_CHECKING:
    from typing_extensions import NotRequired

    class ProcParams(TypedDict):
        """Parameters for BrewHelper.proc()."""

        cmd: NotRequired[str | list[str]]
        print_cmd: NotRequired[bool]
        print_out: NotRequired[bool]
        exit_on_err: NotRequired[bool]
        separate_err: NotRequired[bool]
        print_err: NotRequired[bool]
        env: NotRequired[dict[str, str] | None]
        cwd: NotRequired[str | Path | None]
        dryrun: NotRequired[bool]


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

        self.info: dict[str, dict[str, Any]] | None = None
        self.all_formulae: dict[str, Any] | None = None
        self.formula_aliases: dict[str, dict[str, str]] | None = None
        self.cask_aliases: dict[str, dict[str, str]] | None = None
        self.taps: dict[str, Any] | None = None
        self.leaves_list: list[str] | None = None
        self.leaves_list_on_request: list[str] | None = None

    def readstdout(
        self, proc: subprocess.Popen[str]
    ) -> Generator[str, None, None]:
        if proc.stdout is None:
            return
        for line in iter(proc.stdout.readline, ""):
            line = line.rstrip()
            if line == "":
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
        cmd_orig = " ".join(["$"] + cmd)
        if cmd[0] == "brew":
            cmd[0] = self.opt.get("brew_cmd", "brew")
        if print_cmd or dryrun:
            self.log.info(cmd_orig)
        if dryrun:
            return 0, [" ".join(cmd)]
        all_env = os.environ.copy()
        all_env.update(env)
        lines = []
        try:
            if separate_err:
                if print_err:
                    stderr = None
                else:
                    stderr = subprocess.DEVNULL
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
                    self.log.error(str(e))
            else:
                lines += str(e).splitlines()
                if print_out:
                    self.log.info(str(e))
            ret = e.errno

        if exit_on_err and ret != 0:
            output = "\n".join(lines)
            raise CmdError(
                f"Failed at command: {' '.join(cmd)}\n{output}", ret
            )
        return ret, lines

    def brew_val(self, name: str) -> Any:
        if name not in self.opt:
            _, lines = self.proc("brew --" + name, False, False)
            self.opt[name] = lines[0]
        return self.opt[name]

    def get_info(self) -> dict[str, Any]:
        """Get info of installed brew package."""
        if self.info is None:
            _, lines = self.proc(
                cmd="brew info --json=v2 --installed",
                print_cmd=False,
                print_out=False,
                exit_on_err=True,
                separate_err=True,
            )
            lines = lines[lines.index("{") :]
            data = json.loads("".join(lines))
            self.info = {
                "formulae": {x["name"]: x for x in data["formulae"]},
                "casks": {x["token"]: x for x in data["casks"]},
            }
        return self.info

    def get_all_formulae(self) -> dict[str, Any]:
        """Get info of all formulae."""
        if self.all_formulae is None:
            _, lines = self.proc(
                cmd="brew info --json=v1 --eval-all",
                print_cmd=False,
                print_out=False,
                exit_on_err=True,
                separate_err=True,
            )
            lines = lines[lines.index("[") :]
            data = json.loads("".join(lines))
            self.all_formulae = {x["name"]: x for x in data}
        return self.all_formulae

    def get_formula_list(self) -> list[str]:
        info = self.get_info()
        return list(info["formulae"].keys())

    def get_cask_list(self) -> list[str]:
        info = self.get_info()
        return list(info["casks"].keys())

    def get_formula_aliases(self) -> dict[str, dict[str, str]]:
        if self.formula_aliases is None:
            self.formula_aliases = {}
            info = self.get_info()
            for formula in info["formulae"].values():
                tap = formula["tap"]
                for o in formula.get("oldnames", []):
                    self.formula_aliases[tap] = self.formula_aliases.get(
                        tap, {}
                    )
                    self.formula_aliases[tap][o] = formula["name"]
                for a in formula.get("aliases", []):
                    self.formula_aliases[tap] = self.formula_aliases.get(
                        tap, {}
                    )
                    self.formula_aliases[tap][a] = formula["name"]
        return self.formula_aliases

    def get_cask_aliases(self) -> dict[str, dict[str, str]]:
        if self.cask_aliases is None:
            self.cask_aliases = {}
            info = self.get_info()
            for cask in info["casks"].values():
                tap = cask["tap"]
                for o in cask.get("old_tokens", []):
                    self.cask_aliases[tap] = self.cask_aliases.get(tap, {})
                    self.cask_aliases[tap][o] = cask["name"]
        return self.cask_aliases

    def get_installed(self, package: str) -> dict[str, Any]:
        """Get installed version of brew package."""
        installed = {}
        package_info = self.get_info()["formulae"][package]

        if (version := package_info["linked_keg"]) is None:
            version = package_info["installed"][-1]["version"]

        if version != "":
            for i in package_info["installed"]:
                if i["version"].replace(".reinstall", "") == version:
                    installed = i
                    break
        return installed

    def get_option(self, package: str) -> str:
        """Get install options from brew info."""
        opt = ""
        if used_options := self.get_installed(package).get("used_options", []):
            opt = " " + " ".join(used_options)
        if version := self.get_installed(package).get("version", None):
            info = self.get_info()["formulae"][package]

            for k, v in info.get("versions", {}).items():
                if version == v and k != "stable":
                    if k == "head":
                        opt += " --HEAD"
                    else:
                        opt += " --" + k
        return opt

    def get_tap_packs(
        self, tap: str, alias: bool = False
    ) -> dict[str, list[str]]:
        if self.taps is None:
            _, lines = self.proc(
                cmd="brew tap-info --json --installed",
                print_cmd=False,
                print_out=False,
                exit_on_err=True,
                separate_err=True,
            )
            lines = lines[lines.index("[") :]
            data = json.loads("".join(lines))
            self.taps = {x["name"]: x for x in data}

        packs = {
            "formulae": [
                x.split("/")[-1] for x in self.taps[tap]["formula_names"]
            ],
            "casks": [x.split("/")[-1] for x in self.taps[tap]["cask_tokens"]],
        }
        if alias:
            packs["formulae"] += list(
                self.get_formula_aliases().get(tap, {}).keys()
            )
            packs["casks"] += list(self.get_cask_aliases().get(tap, {}).keys())
        return packs

    def get_leaves(self, on_request: bool = False) -> list[str]:
        if on_request:
            leaves_list = self.leaves_list_on_request
        else:
            leaves_list = self.leaves_list

        if leaves_list is not None:
            return leaves_list

        cmd = "brew leaves"
        if on_request:
            cmd += " --installed-on-request"
        _, lines = self.proc(
            cmd,
            print_cmd=False,
            print_out=False,
            separate_err=True,
            print_err=False,
        )
        leaves_list = [x.split("/")[-1] for x in lines]
        if on_request:
            self.leaves_list_on_request = leaves_list
        else:
            self.leaves_list = leaves_list
        return leaves_list
