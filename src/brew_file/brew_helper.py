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
    from typing_extensions import NotRequired, Unpack

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
    log: logging.Logger = field(
        default_factory=lambda: logging.getLogger(__name__)
    )

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

    def get_formula_list(self) -> list[str]:
        _, lines = self.proc(
            "brew list --formula",
            print_cmd=False,
            print_out=False,
            separate_err=True,
            print_err=False,
        )
        packages = []
        for line in lines:
            if (
                "Warning: nothing to list" in line
                or "=>" in line
                or "->" in line
            ):
                continue
            packages.append(line)
        return packages

    def get_cask_list(self) -> list[str]:
        _, lines = self.proc(
            "brew list --cask",
            print_cmd=False,
            print_out=False,
            separate_err=True,
            print_err=False,
        )
        packages = []
        for line in lines:
            if (
                "Warning: nothing to list" in line
                or "=>" in line
                or "->" in line
            ):
                continue
            packages.append(line)
        return packages

    def brew_info_v1(
        self,
        info_opt: str,
        **kw: Unpack[ProcParams],
    ) -> list[dict[str, Any]]:
        params: ProcParams = {
            "cmd": "brew info --json=v1 " + info_opt,
        }
        params.update(kw)
        _, lines = self.proc(**params)
        info = lines[lines.index("[") :]
        return json.loads("".join(info))

    def brew_info_v2(
        self,
        info_opt: str,
        **kw: Unpack[ProcParams],
    ) -> dict[str, Any]:
        params: ProcParams = {
            "cmd": "brew info --json=v2 " + info_opt,
        }
        params.update(kw)
        _, lines = self.proc(**params)
        info = lines[lines.index("{") :]
        return json.loads("".join(info))

    def get_info(self, package: str = "") -> dict[str, Any]:
        if package == "":
            package = "--installed"
        infotmp = self.brew_info_v1(
            info_opt=package,
            print_cmd=False,
            print_out=False,
            exit_on_err=True,
            separate_err=True,
        )
        info: dict[str, Any] = {}
        for i in infotmp:
            info[i["name"]] = i
        return info

    def get_installed(
        self, package: str, package_info: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Get installed version of brew package."""
        installed = {}
        if package_info is None:
            package_info = self.get_info(package)[package]

        if (version := package_info["linked_keg"]) is None:
            version = package_info["installed"][-1]["version"]

        if version != "":
            for i in package_info["installed"]:
                if i["version"].replace(".reinstall", "") == version:
                    installed = i
                    break
        return installed

    def get_option(
        self, package: str, package_info: dict[str, Any] | None = None
    ) -> str:
        """Get install options from brew info."""
        # Get options for build
        if package_info is None:
            package_info = self.get_info(package)[package]

        opt = ""
        installed = self.get_installed(package, package_info)
        if used_options := installed.get("used_options", []):
            opt = " " + " ".join(used_options)
        for k, v in package_info.get("versions", {}).items():
            if installed.get("version", None) == v and k != "stable":
                if k == "head":
                    opt += " --HEAD"
                else:
                    opt += " --" + k
        return opt

    def get_formula_info(self) -> list[dict[str, Any]]:
        if "formula_info" in self.opt:
            return self.opt["formula_info"]

        info = self.brew_info_v1(
            info_opt="--eval-all", print_cmd=False, print_out=False
        )
        if (
            not [x for x in info if x["tap"] == self.opt["core_repo"]]
            and self.opt["api"]
        ):
            formula_json = Path(self.opt["cache"]) / "api" / "formula.jws.json"
            if not formula_json.exists():
                _ = self.proc("brew update")
            with open(formula_json, "r") as f:
                info_api = json.loads(json.load(f)["payload"])
            info = info_api + info
        self.opt["formula_info"] = info
        return info

    def get_formula_aliases(self) -> dict[str, str]:
        if "formula_aliases" in self.opt:
            return self.opt["formula_aliases"]
        info = self.get_formula_info()
        self.opt["formula_aliases"] = {}
        for i in info:
            if "aliases" in i:
                for a in i["aliases"]:
                    self.opt["formula_aliases"][a] = i["name"]
        return self.opt["formula_aliases"]

    def get_tap_packs(self, tap: str) -> list[str]:
        packs = [x["name"] for x in self.get_formula_info() if x["tap"] == tap]
        packs_aliases = [
            k for k, v in self.get_formula_aliases().items() if v in packs
        ]
        return packs + packs_aliases

    def get_cask_info(self) -> Any:
        if "cask_info" in self.opt:
            return self.opt["cask_info"]

        _, lines = self.proc(
            "brew info --eval-all --json=v2",
            print_cmd=False,
            print_out=False,
        )
        info = self.brew_info_v2(
            info_opt="--eval-all", print_cmd=False, print_out=False
        )["casks"]
        if (
            not [x for x in info if x["tap"] == self.opt["cask_repo"]]
            and self.opt["api"]
        ):
            cask_json = Path(self.opt["cache"]) / "api" / "cask.jws.json"
            if not cask_json.exists():
                _ = self.proc("brew update")
            with open(cask_json, "r") as f:
                info_api = json.loads(json.load(f)["payload"])
            info = info_api + info
        self.opt["cask_info"] = info
        return info

    def get_tap_casks(self, tap: str) -> list[str]:
        return sorted(
            [x["token"] for x in self.get_cask_info() if x["tap"] == tap]
        )

    def get_leaves(self, on_request: bool = False) -> list[str]:
        var_name = f"leaves_list_{on_request}"
        if var_name in self.opt:
            return self.opt[var_name]
        cmd = "brew leaves"
        if on_request:
            cmd += " --installed-on-request"
        _, leaves_list = self.proc(
            cmd,
            print_cmd=False,
            print_out=False,
            separate_err=True,
            print_err=False,
        )
        leaves_list = [x.split("/")[-1] for x in leaves_list]
        self.opt[var_name] = leaves_list
        return leaves_list
