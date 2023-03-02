from __future__ import annotations

import json
import logging
import os
import shlex
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Generator


class CmdError(Exception):
    """Exception at command execution."""

    def __init__(self, message, return_code) -> None:
        super().__init__(message)
        self.return_code = return_code


@dataclass
class BrewHelper:
    """Helper functions for BrewFile."""

    opt: dict = field(default_factory=dict)
    log: logging.Logger = field(
        default_factory=lambda: logging.getLogger(__name__)
    )

    def readstdout(self, proc: subprocess.Popen) -> Generator[str, None, None]:
        for line in iter(proc.stdout.readline, ""):  # type: ignore
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
        env: dict | None = None,
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
            self.opt[name] = self.proc("brew --" + name, False, False)[1][0]
        return self.opt[name]

    def get_formula_list(self):
        lines = self.proc(
            "brew list --formula",
            print_cmd=False,
            print_out=False,
            separate_err=True,
            print_err=False,
        )[1]
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

    def get_cask_list(self):
        lines = self.proc(
            "brew list --cask",
            print_cmd=False,
            print_out=False,
            separate_err=True,
            print_err=False,
        )[1]
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

    def get_info(self, package: str = "") -> dict:
        if package == "":
            package = "--installed"
        infotmp = json.loads(
            "".join(
                self.proc(
                    "brew info --json=v1 " + package,
                    print_cmd=False,
                    print_out=False,
                    exit_on_err=True,
                    separate_err=True,
                )[1]
            )
        )
        info = {}
        for i in infotmp:
            info[i["name"]] = i
        return info

    def get_installed(
        self, package: str, package_info: dict | None = None
    ) -> dict:
        """Get installed version of brew package."""
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
        self, package: str, package_info: dict | None = None
    ) -> str:
        """Get install options from brew info."""
        # Get options for build
        if package_info is None:
            package_info = self.get_info(package)[package]

        opt = ""
        installed = self.get_installed(package, package_info)
        if installed["used_options"]:
            opt = " " + " ".join(installed["used_options"])
        for k, v in package_info["versions"].items():
            if installed["version"] == v and k != "stable":
                if k == "head":
                    opt += " --HEAD"
                else:
                    opt += " --" + k
        return opt

    def get_formula_info(self):
        if "formula_info" in self.opt:
            return self.opt["formula_info"]

        _, lines = self.proc(
            "brew info --eval-all --json=v1",
            print_cmd=False,
            print_out=False,
        )
        info = list(json.loads("".join(lines)))
        if self.opt["api"]:
            info_taps = [x for x in info if x["tap"] != self.opt["core_repo"]]
            formula_json = Path(self.opt["cache"]) / "api" / "formula.jws.json"
            if not formula_json.exists():
                self.proc("brew update")
            with open(formula_json, "r") as f:
                info_api = json.loads(json.load(f)["payload"])
            info = info_api + info_taps
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

    def get_tap_packs(self, tap: str) -> list:
        packs = [x["name"] for x in self.get_formula_info() if x["tap"] == tap]
        packs_aliases = [
            k for k, v in self.get_formula_aliases().items() if v in packs
        ]
        return packs + packs_aliases

    def get_cask_info(self):
        if "cask_info" in self.opt:
            return self.opt["cask_info"]

        _, lines = self.proc(
            "brew info --eval-all --json=v2",
            print_cmd=False,
            print_out=False,
        )
        info = list(json.loads("".join(lines))["casks"])
        if self.opt["api"]:
            info_taps = [x for x in info if x["tap"] != self.opt["cask_repo"]]
            cask_json = Path(self.opt["cache"]) / "api" / "cask.jws.json"
            if not cask_json.exists():
                self.proc("brew update")
            with open(cask_json, "r") as f:
                info_api = json.loads(json.load(f)["payload"])
            info = info_api + info_taps
        self.opt["cask_info"] = info
        return info

    def get_tap_casks(self, tap: str) -> list:
        return sorted(
            [x["token"] for x in self.get_cask_info() if x["tap"] == tap]
        )

    def get_leaves(self) -> list[str]:
        if "leaves" in self.opt:
            return self.opt["leaves"]
        leaves = self.proc(
            "brew leaves",
            print_cmd=False,
            print_out=False,
            separate_err=True,
            print_err=False,
        )[1]
        leaves = [x.split("/")[-1] for x in leaves]
        self.opt["leaves"] = leaves
        return leaves
