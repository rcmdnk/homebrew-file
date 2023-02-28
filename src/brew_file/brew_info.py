from __future__ import annotations

import copy
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Union

from .brew_helper import BrewHelper
from .utils import is_mac


@dataclass
class BrewInfo:
    """Homebrew information storage."""

    helper: BrewHelper
    file: Path = field(default_factory=lambda: Path())
    log: logging.Logger = field(
        default_factory=lambda: logging.getLogger(__name__)
    )

    def __post_init__(self) -> None:
        self.brew_input_opt: dict[str, str] = {}

        self.brew_input: list[str] = []
        self.tap_input: list[str] = []
        self.cask_input: list[str] = []
        self.appstore_input: list[str] = []
        self.main_input: list[str] = []
        self.file_input: list[str] = []

        self.before_input: list[str] = []
        self.after_input: list[str] = []
        self.cmd_input: list[str] = []

        self.cask_args_input: dict[str, str] = {}

        self.brew_list_opt: dict[str, str] = {}

        self.brew_list: list[str] = []
        self.brew_full_list: list[str] = []
        self.tap_list: list[str] = []
        self.cask_list: list[str] = []
        self.appstore_list: list[str] = []
        self.main_list: list[str] = []
        self.file_list: list[str] = []

        self.cask_nocask_list: list[str] = []

        self.list_dic: dict[str, list[str] | dict[str, str]] = {
            "brew_input_opt": self.brew_input_opt,
            "brew_input": self.brew_input,
            "tap_input": self.tap_input,
            "cask_input": self.cask_input,
            "appstore_input": self.appstore_input,
            "main_input": self.main_input,
            "file_input": self.file_input,
            "before_input": self.before_input,
            "after_input": self.after_input,
            "cmd_input": self.cmd_input,
            "cask_args_input": self.cask_args_input,
            "brew_list_opt": self.brew_list_opt,
            "brew_list": self.brew_list,
            "brew_full_list": self.brew_full_list,
            "tap_list": self.tap_list,
            "cask_list": self.cask_list,
            "cask_nocask_list": self.cask_nocask_list,
            "appstore_list": self.appstore_list,
            "main_list": self.main_list,
            "file_list": self.file_list,
        }

    def get_dir(self) -> Path:
        return self.file.parent

    def check_file(self) -> bool:
        return self.file.exists()

    def check_dir(self) -> bool:
        return self.get_dir().exists()

    def clear_input(self) -> None:
        self.brew_input_opt.clear()

        del self.brew_input[:]
        del self.tap_input[:]
        del self.cask_input[:]
        del self.appstore_input[:]
        del self.main_input[:]
        del self.file_input[:]

        del self.before_input[:]
        del self.after_input[:]
        del self.cmd_input[:]

        self.cask_args_input.clear()

    def clear_list(self) -> None:
        self.brew_list_opt.clear()

        del self.brew_list[:]
        del self.brew_full_list[:]
        del self.tap_list[:]
        del self.cask_list[:]
        del self.cask_nocask_list[:]
        del self.appstore_list[:]
        del self.main_list[:]
        del self.file_list[:]

    def clear(self) -> None:
        self.clear_input()
        self.clear_list()

    def input_to_list(self) -> None:
        self.clear_list()
        self.brew_list.extend(self.brew_input)
        self.brew_list_opt.update(self.brew_input_opt)
        self.tap_list.extend(self.tap_input)
        self.cask_list.extend(self.cask_input)
        self.appstore_list.extend(self.appstore_input)
        self.main_list.extend(self.main_input)
        self.file_list.extend(self.file_input)

    def sort(self) -> None:
        core_tap = []
        cask_tap = []
        brew_taps = []
        other_taps = []
        for t in self.tap_list:
            if t == self.helper.opt["core_repo"]:
                core_tap.append(t)
            elif t == self.helper.opt["cask_repo"]:
                cask_tap.append(t)
            elif t.startswith(self.helper.opt["homebrew_tap_prefix"]):
                brew_taps.append(t)
            else:
                other_taps.append(t)
        brew_taps.sort()
        other_taps.sort()
        self.tap_list = core_tap + cask_tap + brew_taps + other_taps

        self.brew_list.sort()
        self.brew_full_list.sort()
        self.cask_list.sort()
        self.main_list.sort()
        self.file_list.sort()
        self.cask_nocask_list.sort()

        self.appstore_list.sort(
            key=lambda x: x.split()[1].lower()
            if len(x.split()) > 1
            else x.split()[0]
        )

    def get(self, name: str) -> Union[list, dict]:
        return copy.deepcopy(self.list_dic[name])

    def get_files(self) -> dict:
        self.read()
        files = {"main": self.get("main_input")}
        files.update({"ext": self.get("file_input")})
        return files

    def remove(self, name: str, package: str) -> None:
        collection = self.list_dic[name]
        if isinstance(collection, list):
            collection.remove(package)
        elif isinstance(collection, dict):
            del collection[package]

    def set_val(self, name: str, val: list | dict) -> None:
        collection = self.list_dic[name]
        if isinstance(collection, list):
            del collection[:]
            collection.extend(val)
        elif isinstance(collection, dict):
            collection.clear()
            collection.update(val)

    def add(self, name: str, val: list | dict) -> None:
        collection = self.list_dic[name]
        if isinstance(collection, list):
            collection.extend([x for x in val if x not in collection])
        elif isinstance(collection, dict):
            collection.update(val)

    def read(self) -> None:
        self.clear_input()

        if not self.file.exists():
            return
        with open(self.file, "r") as f:
            lines = f.readlines()
            is_ignore = False
            self.tap_input.append("direct")
            for line in lines:
                if re.match("# *BREWFILE_ENDIGNORE", line):
                    is_ignore = False
                if re.match("# *BREWFILE_IGNORE", line):
                    is_ignore = True
                if is_ignore:
                    continue
                if (
                    re.match(" *$", line) is not None
                    or re.match(" *#", line) is not None
                ):
                    continue
                args = (
                    line.replace("'", "")
                    .replace('"', "")
                    .replace(",", " ")
                    .replace("[", "")
                    .replace("]", "")
                    .split()
                )
                cmd = args[0]
                p = args[1] if len(args) > 1 else ""
                if len(args) > 2 and p in ["tap", "cask"]:
                    args.pop(0)
                    cmd = args[0]
                    p = args[1]
                    if not self.helper.opt.get("form"):
                        self.helper.opt["form"] = "cmd"
                if (
                    len(args) > 2
                    and cmd in ["brew", "cask"]
                    and p == "install"
                ):
                    args.pop(1)
                    p = args[1]
                    if not self.helper.opt.get("form"):
                        self.helper.opt["form"] = "cmd"

                if len(args) > 2:
                    if args[2] == "args:":
                        opt = (
                            " "
                            + " ".join(["--" + x for x in args[3:]]).strip()
                        )
                        if not self.helper.opt.get("form"):
                            self.helper.opt["form"] = "bundle"
                    else:
                        opt = " " + " ".join(args[2:]).strip()
                else:
                    opt = ""
                excmd = " ".join(line.split()[1:]).strip()

                if not self.helper.opt.get("form"):
                    if cmd in ["brew", "tap", "tapall"]:
                        if '"' in line or "'" in line:
                            self.helper.opt["form"] = "bundle"

                cmd = cmd.lower()
                if cmd in ["brew", "install"]:
                    self.brew_input.append(p)
                    self.brew_input_opt[p] = opt
                elif cmd == "tap":
                    self.tap_input.append(p)
                elif cmd == "tapall":
                    self.helper.proc(f"brew tap {p}")
                    self.tap_input.append(p)
                    for tp in self.helper.get_tap_packs(p):
                        self.brew_input.append(tp)
                        self.brew_input_opt[tp] = ""
                    if is_mac():
                        for tp in self.helper.get_tap_casks(p):
                            self.cask_input.append(tp)
                elif cmd == "cask":
                    self.cask_input.append(p)
                elif cmd == "mas" and line.find(",") != -1:
                    if not self.helper.opt.get("form"):
                        self.helper.opt["form"] = "bundle"
                    p = line.split()[1].strip(",").strip("'").strip('"')
                    pid = line.split()[3]
                    self.appstore_input.append(pid + " " + p)
                elif cmd in ["appstore", "mas"]:
                    self.appstore_input.append(
                        re.sub("^ *appstore *", "", line)
                        .strip()
                        .strip("'")
                        .strip('"')
                    )
                elif cmd == "main":
                    self.main_input.append(p)
                    self.file_input.append(p)
                elif cmd in ["file", "brewfile"]:
                    self.file_input.append(p)
                elif cmd == "before":
                    self.before_input.append(excmd)
                elif cmd == "after":
                    self.after_input.append(excmd)
                elif cmd == "cask_args":
                    if self.helper.opt.get("form") in [
                        "brewdler",
                        "bundle",
                    ]:
                        for arg in excmd.split(","):
                            k = f"--{arg.split(':')[0]}"
                            v = arg.split(":")[1]
                            if v == "true":
                                v = ""
                            self.cask_args_input[k] = v
                    else:
                        for arg in excmd.split():
                            k = arg.split(":")[0]
                            v = arg.split("=")[1] if "=" in arg else ""
                            self.cask_args_input[k] = v
                else:
                    self.cmd_input.append(line.strip())

    def convert_option(self, opt: str) -> str:
        if opt != "" and self.helper.opt["form"] in ["brewdler", "bundle"]:
            opt = (
                ", args: ["
                + ", ".join(
                    ["'" + re.sub("^--", "", x) + "'" for x in opt.split()]
                )
                + "]"
            )
        return opt

    def packout(self, pack: str) -> str:
        if self.helper.opt["form"] in ["brewdler", "bundle"]:
            return "'" + pack + "'"
        return pack

    def mas_pack(self, pack: str) -> str:
        if self.helper.opt["form"] in ["brewdler", "bundle"]:
            pack_split = pack.split()
            pid = pack_split[0]
            name = pack_split[1:]
            return "'" + " ".join(name) + "', id: " + pid
        return pack

    def write(self) -> None:
        output_prefix = ""
        output = ""

        # commands for each format
        # if self.helper.opt["form"] in ["file", "none"]:
        cmd_before = "before "
        cmd_after = "after "
        cmd_cask_args = "cask_args "
        cmd_other = ""
        cmd_install = "brew "
        cmd_tap = "tap "
        cmd_cask = "cask "
        cmd_cask_nocask = "#cask "
        cmd_appstore = "appstore "
        cmd_main = "main "
        cmd_file = "file "
        if self.helper.opt["form"] in ["brewdler", "bundle"]:
            cmd_before = "#before "
            cmd_after = "#after "
            cmd_cask_args = "#cask_args "
            cmd_other = "#"
            cmd_cask_nocask = "#cask "
            cmd_appstore = "mas "
            cmd_main = "#main "
            cmd_file = "#file "
        elif self.helper.opt["form"] in ["command", "cmd"]:
            # Shebang for command format
            output_prefix += """#!/usr/bin/env bash

#BREWFILE_IGNORE
if ! which brew >& /dev/null;then
  brew_installed=0
  echo Homebrew is not installed!
  echo Install now...
  echo /bin/bash -c \\\"\\$\\(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh\\)\\\"
  /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)\"
  echo
fi
#BREWFILE_ENDIGNORE

"""

            cmd_before = ""
            cmd_after = ""
            cmd_other = ""
            cmd_install = "brew install "
            cmd_tap = "brew tap "
            cmd_cask = "brew install "
            cmd_cask_nocask = "#brew install "
            cmd_appstore = "mas install "
            cmd_main = "#main "
            cmd_file = "#file "

        # sort
        self.sort()

        # Before commands
        if self.before_input:
            output += "# Before commands\n"
            for c in self.before_input:
                output += cmd_before + c + "\n"

        # Cask args
        if self.cask_args_input:
            output += "\n# Cask args\n"
            delimiter = ""
            for k, v in self.cask_args_input.items():
                output += cmd_cask_args
                if self.helper.opt["form"] in ["brewdler", "bundle"]:
                    if v == "":
                        output += f"{delimiter}{k.removeprefix('--')}: true"
                    else:
                        output += f"{delimiter}{k.removeprefix('--')}: {v}"
                    delimiter = ", "
                else:
                    output += f"{delimiter}{k}"
                    if v != "":
                        output += f"={v}"
                    delimiter = " "
            output += "\n"

        # Taps
        if self.tap_list:
            isfirst = True

            def first_tap_pack_write(
                isfirst, direct_first, isfirst_pack, tap, cmd_tap
            ):
                output = ""
                if isfirst:
                    output += "\n# tap repositories and their packages\n"
                if not direct_first and isfirst_pack:
                    output += "\n" + cmd_tap + self.packout(tap) + "\n"
                return output

            for t in self.tap_list:
                isfirst_pack = True
                direct_first = False
                tap_packs = self.helper.get_tap_packs(t)

                if t == "direct":
                    if not tap_packs:
                        continue
                    direct_first = True

                if not self.helper.opt["caskonly"]:
                    output += first_tap_pack_write(
                        isfirst, direct_first, isfirst_pack, t, cmd_tap
                    )
                    isfirst = isfirst_pack = False

                    for p in self.brew_list[:]:
                        if p.split("/")[-1].replace(".rb", "") in tap_packs:
                            if direct_first:
                                direct_first = False
                                output += "\n## " + "Direct install\n"
                            pack = self.packout(p) + self.convert_option(
                                self.brew_list_opt[p]
                            )
                            output += cmd_install + pack + "\n"
                            self.brew_list.remove(p)
                            del self.brew_list_opt[p]
                if not is_mac():
                    continue
                tap_casks = self.helper.get_tap_casks(t)
                for p in self.cask_list[:]:
                    if p in tap_casks:
                        output += first_tap_pack_write(
                            isfirst, False, isfirst_pack, t, cmd_tap
                        )
                        isfirst = isfirst_pack = False
                        output += cmd_cask + self.packout(p) + "\n"
                        self.cask_list.remove(p)

        # Brew packages
        if not self.helper.opt["caskonly"] and self.brew_list:
            output += "\n# Other Homebrew packages\n"
            for p in self.brew_list:
                pack = self.packout(p) + self.convert_option(
                    self.brew_list_opt[p]
                )
                output += cmd_install + pack + "\n"

        # Casks
        if is_mac() and self.cask_list:
            output += "\n# Other Cask applications\n"
            for c in self.cask_list:
                output += cmd_cask + self.packout(c) + "\n"

        # Installed by cask, but cask files were not found...
        if is_mac() and self.cask_nocask_list:
            output += "\n# Below applications were installed by Cask,\n"
            output += "# but do not have corresponding casks.\n\n"
            for c in self.cask_nocask_list:
                output += cmd_cask_nocask + self.packout(c) + "\n"

        # App Store applications
        if is_mac() and self.helper.opt["appstore"] and self.appstore_list:
            output += "\n# App Store applications\n"
            for a in self.appstore_list:
                output += cmd_appstore + self.mas_pack(a) + "\n"

        # Main file
        if self.main_list:
            output += "\n# Main file\n"
            for f in self.main_list:
                output += cmd_main + self.packout(f) + "\n"

        # Additional files
        if len(self.file_list) > len(self.main_list):
            output += "\n# Additional files\n"
            for f in self.file_list:
                if f not in self.main_list:
                    output += cmd_file + self.packout(f) + "\n"

        # Other commands
        if self.cmd_input:
            output += "\n# Other commands\n"
            for c in self.cmd_input:
                output += cmd_other + c + "\n"

        # After commands
        if self.after_input:
            output += "\n# After commands\n"
            for c in self.after_input:
                output += cmd_after + c + "\n"

        # Write to Brewfile
        if output:
            output = output_prefix + output
            self.get_dir().mkdir(parents=True, exist_ok=True)
            with open(self.file, "w") as fout:
                fout.write(output)
            self.log.info(output)

        # Change permission for exe/normal file
        if self.helper.opt["form"] in ["command", "cmd"]:
            self.helper.proc(
                f"chmod 755 {self.file}",
                print_cmd=False,
                print_out=False,
                exit_on_err=False,
            )
        else:
            self.helper.proc(
                f"chmod 644 {self.file}",
                print_cmd=False,
                print_out=False,
                exit_on_err=False,
            )
