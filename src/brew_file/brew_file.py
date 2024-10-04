from __future__ import annotations

import copy
import logging
import os
import re
import shlex
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Literal, Tuple, cast
from urllib.parse import quote

from .brew_helper import BrewHelper
from .brew_info import BrewInfo
from .info import __prog__
from .utils import OpenWrapper, expandpath, home_tilde, is_mac, to_bool, to_num

CaskInfo = Dict[str, Tuple[str, str]]
CaskListInfo = Dict[str, List[Tuple[str, str]]]


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
        xdg_config_home = os.getenv("XDG_CONFIG_HOME")
        if xdg_config_home is not None:
            input_path = Path(xdg_config_home) / "brewfile/Brewfile"
            if input_path.is_file():
                return input_path
        home_config = Path(os.environ["HOME"]) / ".config/brewfile/Brewfile"
        if home_config.is_file():
            return home_config
        if input_path is None:
            input_path = home_config

        home_brewfile = Path(os.environ["HOME"]) / "/.brewfile/Brewfile"
        if home_brewfile.is_file():
            return home_brewfile
        return input_path

    def parse_env_opts(
        self, env_var: str, base_opts: dict[str, Any] | None = None
    ) -> dict[str, str]:
        """Return a dictionary parsed from an environment variable."""
        opts: dict[str, Any] = {}
        if base_opts is not None:
            opts.update(base_opts)

        env_opts = os.getenv(env_var, None)
        if env_opts:
            user_opts = dict(
                pair.partition("=")[::2] for pair in env_opts.split()
            )

            if user_opts:
                opts.update(user_opts)
            else:
                self.log.warning(
                    '{env_var}: "{env_opts}" is not a proper format.'
                )
                self.log.warning("Ignoring the value.\n")
        return opts

    def default_opt(self) -> dict[str, Any]:
        opt: dict[str, Any] = {}
        opt["verbose"] = os.getenv("HOMEBREW_BREWFILE_VERBOSE", "info")
        opt["command"] = ""
        opt["input"] = Path(os.getenv("HOMEBREW_BREWFILE", ""))
        if not opt["input"].name:
            opt["input"] = self.get_input_path()
        opt["backup"] = os.getenv("HOMEBREW_BREWFILE_BACKUP", "")
        opt["form"] = None
        opt["leaves"] = to_bool(os.getenv("HOMEBREW_BREWFILE_LEAVES", False))
        opt["on_request"] = to_bool(
            os.getenv("HOMEBREW_BREWFILE_ON_REQUEST", False)
        )
        opt["top_packages"] = os.getenv("HOMEBREW_BREWFILE_TOP_PACKAGES", "")
        opt["fetch_head"] = to_bool(
            os.getenv("HOMEBREW_BREWFILE_FETCH_HEAD", False)
        )
        opt["repo"] = ""
        opt["noupgradeatupdate"] = False
        opt["link"] = True
        opt["caskonly"] = False
        opt["dryrun"] = False
        opt["initialized"] = False
        opt["homebrew_tap_prefix"] = "homebrew/"
        opt["core_repo"] = f"{opt['homebrew_tap_prefix']}core"
        opt["cask_repo"] = f"{opt['homebrew_tap_prefix']}cask"
        opt["reattach_formula"] = "reattach-to-user-namespace"
        opt["mas_formula"] = "mas"
        opt["whalebrew_formula"] = "whalebrew"
        opt["vscode_formula"] = "vscode"
        opt["my_editor"] = os.getenv(
            "HOMEBREW_BREWFILE_EDITOR", os.getenv("EDITOR", "vim")
        )
        opt["brew_cmd"] = ""
        opt["mas_cmd"] = "mas"
        opt["is_mas_cmd"] = 0
        opt["mas_cmd_installed"] = False
        opt["reattach_cmd_installed"] = False
        opt["whalebrew_cmd"] = "whalebrew"
        opt["is_whalebrew_cmd"] = 0
        opt["whalebrew_cmd_installed"] = False
        opt["vscode_cmd"] = "code"
        opt["is_vscode_cmd"] = 0
        opt["vscode_cmd_installed"] = False
        opt["docker_running"] = 0
        opt["args"] = []
        opt["yn"] = False
        opt["brew_packages"] = ""
        opt["homebrew_ruby"] = False

        # Check Homebrew variables
        # Boolean HOMEBREW variable should be True if other than empty is set, including '0'
        opt["api"] = not os.getenv("HOMEBREW_NO_INSTALL_FROM_API", False)
        opt["cache"] = self.helper.brew_val("cache")
        opt["caskroom"] = self.helper.brew_val("prefix") + "/Caskroom"
        cask_opts = self.parse_env_opts(
            "HOMEBREW_CASK_OPTS", {"--appdir": "", "--fontdir": ""}
        )
        opt["appdir"] = (
            cask_opts["--appdir"].rstrip("/")
            if cask_opts["--appdir"] != ""
            else os.environ["HOME"] + "/Applications"
        )
        opt["appdirlist"] = [
            "/Applications",
            os.environ["HOME"] + "/Applications",
        ]
        if opt["appdir"].rstrip("/") not in opt["appdirlist"]:
            opt["appdirlist"].append(opt["appdir"])
        opt["appdirlist"] += [
            x.rstrip("/") + "/Utilities" for x in opt["appdirlist"]
        ]
        opt["appdirlist"] = [x for x in opt["appdirlist"] if Path(x).is_dir()]
        # fontdir may be used for application search, too
        opt["fontdir"] = cask_opts["--fontdir"]

        opt["appstore"] = to_num(os.getenv("HOMEBREW_BREWFILE_APPSTORE", -1))
        opt["no_appstore"] = False

        opt["whalebrew"] = to_num(os.getenv("HOMEBREW_BREWFILE_WHALEBREW", 0))
        opt["vscode"] = to_num(os.getenv("HOMEBREW_BREWFILE_VSCODE", 0))

        opt["all_files"] = False
        opt["read"] = False

        return opt

    def set_input(self, file: str | Path) -> None:
        self.opt["input"] = Path(file)
        self.brewinfo = BrewInfo(self.helper, self.opt["input"])
        self.brewinfo_ext: list[BrewInfo] = []
        self.brewinfo_main = self.brewinfo

    def banner(self, text: str, debug_out: bool = False) -> None:
        width = 0
        for line in text.split("\n"):
            if width < len(line):
                width = len(line)
        output = f"\n{'#' * width}\n{text}\n{'#' * width}\n"
        if debug_out:
            self.log.debug(output)
        else:
            self.log.info(output)

    @dataclass
    class DryrunBanner:
        """Dryrun banner context manager."""

        brewfile: BrewFile

        def __enter__(self) -> None:
            if self.brewfile.opt["dryrun"]:
                self.brewfile.banner("# This is dry run.")

        def __exit__(
            self, exc_type: Any, exc_value: Any, traceback: Any
        ) -> None:
            if self.brewfile.opt["dryrun"]:
                self.brewfile.banner("# This is dry run.")

    def set_verbose(self, verbose: str | None = None) -> None:
        if verbose is None:
            self.opt["verbose"] = os.getenv(
                "HOMEBREW_BREWFILE_VERBOSE", "info"
            )
        else:
            self.opt["verbose"] = verbose
        # Keep compatibility with old verbose
        if self.opt["verbose"] == "0":
            self.opt["verbose"] = "debug"
        elif self.opt["verbose"] == "1":
            self.opt["verbose"] = "info"
        elif self.opt["verbose"] == "2":
            self.opt["verbose"] = "error"

        if self.log.parent and self.log.parent.name != "root":
            self.log.parent.setLevel(
                getattr(logging, self.opt["verbose"].upper())
            )
        else:
            self.log.setLevel(getattr(logging, self.opt["verbose"].upper()))

    def set_args(self, **kw: str) -> None:
        """Set arguments."""
        self.opt.update(kw)

        self.set_verbose(self.opt.get("verbose", None))
        for k in self.int_opts:
            self.opt[k] = int(self.opt[k])
        for k in self.float_opts:
            self.opt[k] = float(self.opt[k])

        # fix appstore option
        appstore = 1
        if self.opt["appstore"] != -1:
            appstore = self.opt["appstore"]
        elif self.opt["no_appstore"]:
            appstore = 0
        self.opt["appstore"] = to_num(appstore)

        self.set_input(self.opt["input"])

    def ask_yn(self, question: str) -> bool:
        """Helper for yes/no."""
        if self.opt["yn"]:
            self.log.info(f"{question} [y/n]: y")
            return True

        yes = ["yes", "y", ""]
        no = ["no", "n"]

        yn = input(f"{question} [y/n]: ").lower()
        while True:
            if yn in yes:
                return True
            if yn in no:
                return False
            yn = input("Answer with yes (y) or no (n): ").lower()

    def read_all(self, force: bool = False) -> None:
        if not force and self.opt["read"]:
            return
        self.brewinfo_ext = [self.brewinfo]
        main = self.read(self.brewinfo, is_main=True)
        if not main:
            raise RuntimeError("Cannot find main Brewfile.")
        self.brewinfo_main = main
        self.brewinfo_ext.remove(self.brewinfo_main)
        for cmd in ["mas", "reattach", "whalebrew", "vscode"]:
            if self.opt[f"{cmd}_cmd_installed"]:
                p = Path(self.opt["{cmd}_formula"]).name
                if p not in self.get_list("brew_input"):
                    self.brewinfo_main.brew_input.append(p)
                    self.brewinfo_main.brew_input_opt[p] = ""
        self.opt["read"] = True

    def read(
        self, brewinfo: BrewInfo, is_main: bool = False
    ) -> BrewInfo | None:
        if is_main:
            main = brewinfo
        else:
            main = None
        files = brewinfo.get_files()
        for f in files["ext"]:
            is_next_main = f in files["main"]
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
        self.brewinfo_main.add_to_list("brew_list", self.brewinfo.brew_list)
        self.brewinfo_main.add_to_list(
            "brew_full_list", self.brewinfo.brew_list
        )
        self.brewinfo_main.add_to_list("tap_list", self.brewinfo.tap_list)
        self.brewinfo_main.add_to_list("cask_list", self.brewinfo.cask_list)
        self.brewinfo_main.add_to_list(
            "cask_nocask_list", self.brewinfo.cask_nocask_list
        )
        self.brewinfo_main.add_to_list(
            "appstore_list", self.brewinfo.appstore_list
        )
        self.brewinfo_main.add_to_list(
            "whalebrew_list", self.brewinfo.whalebrew_list
        )
        self.brewinfo_main.add_to_list(
            "vscode_list", self.brewinfo.vscode_list
        )
        self.brewinfo_main.add_to_dict(
            "brew_list_opt", self.brewinfo.brew_list_opt
        )

    def input_to_list(self, only_ext: bool = False) -> None:
        if not only_ext:
            self.brewinfo_main.input_to_list()
        for b in self.brewinfo_ext:
            b.input_to_list()

    def write(self, debug_out: bool = False) -> None:
        self.banner(
            f"# Initialize {self.brewinfo_main.file}", debug_out=debug_out
        )
        self.brewinfo_main.write()
        for b in self.brewinfo_ext:
            self.banner(f"# Initialize {b.file}", debug_out=debug_out)
            b.write()

    def get_list(self, name: str, only_ext: bool = False) -> set[str]:
        list_copy = self.brewinfo_main.get_list(name)
        if only_ext:
            del list_copy[:]
        for b in self.brewinfo_ext:
            list_copy += b.get_list(name)
        return set(list_copy)

    def get_dict(self, name: str, only_ext: bool = False) -> dict[str, str]:
        dict_copy = self.brewinfo_main.get_dict(name)
        if only_ext:
            dict_copy.clear()
        for b in self.brewinfo_ext:
            dict_copy.update(b.get_dict(name))
        return dict_copy

    def remove_pack(self, name: str, package: str) -> None:
        if package in self.brewinfo_main.get_list(name):
            self.brewinfo_main.remove(name, package)
        else:
            for b in self.brewinfo_ext:
                if package in b.get_list(name):
                    b.remove(name, package)

    def repo_name(self) -> str:
        return self.opt["repo"].split("/")[-1].split(".git")[0]

    def user_name(self) -> str:
        user = ""
        repo_split = self.opt["repo"].split("/")
        if len(repo_split) > 1:
            user = repo_split[-2].split(":")[-1]
        if not user:
            _, lines = self.helper.proc(
                "git config --get github.user",
                print_cmd=False,
                print_out=False,
                exit_on_err=False,
                separate_err=False,
            )
            if lines:
                user = lines[0]
            else:
                _, lines = self.helper.proc(
                    "git config --get user.name",
                    print_cmd=False,
                    print_out=False,
                    exit_on_err=False,
                    separate_err=False,
                )
                if lines:
                    user = lines[0]
                else:
                    user = ""
            if not user:
                raise RuntimeError("Can not find git (github) user name")
        return user

    def input_dir(self) -> Path:
        return self.opt["input"].parent

    def input_file(self) -> str:
        return self.opt["input"].name

    def repo_file(self) -> Path:
        """Helper to build Brewfile path for the repository."""
        return Path(
            self.input_dir(),
            self.user_name() + "_" + self.repo_name(),
            self.input_file(),
        )

    def init_repo(self) -> None:
        dirname = Path(self.brewinfo.get_dir())
        _, branches = self.helper.proc(
            "git branch",
            print_cmd=False,
            print_out=False,
            exit_on_err=True,
            separate_err=True,
            cwd=dirname,
        )
        if branches:
            return

        self.log.info("Initialize the repository with README.md/Brewfile.")
        readme = dirname / "README.md"
        if not readme.exists():
            f = open(readme, "w")
            f.write(
                "# " + self.repo_name() + "\n\n"
                "Package list for [homebrew](http://brew.sh/).\n\n"
                "Managed by "
                "[homebrew-file](https://github.com/rcmdnk/homebrew-file)."
            )
            f.close()
        self.brewinfo.file.touch()

        if self.check_gitconfig():
            _ = self.helper.proc("git add -A", cwd=dirname)
            _ = self.helper.proc(
                ["git", "commit", "-m", '"Prepared by ' + __prog__ + '"'],
                cwd=dirname,
            )
            _, lines = self.helper.proc("git config init.defaultBranch")
            default_branch = lines[0]
            self.helper.proc(
                f"git push -u origin {default_branch}", cwd=dirname
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
                raise RuntimeError(
                    f"Can not clone {self.opt['repo']}.\n"
                    "please check the repository, or reset with\n"
                    f"    $ {__prog__} set_repo"
                )
            else:
                return False
        self.init_repo()
        return True

    def check_github_repo(self) -> None:
        """Helper to check and create GitHub repository."""
        # Check if the repository already exists or not.
        if self.clone_repo(exit_on_err=False):
            return

        # Create new repository #
        raise RuntimeError(
            f"GitHub repository: {self.user_name()}/{self.repo_name()} doesn't exist.\n"
            "Please create the repository first, then try again"
        )

    def check_local_repo(self) -> None:
        dirname = self.opt["repo"].replace("file:///", "")
        Path(dirname).mkdir(parents=True, exist_ok=True)
        _ = self.helper.proc("git init", cwd=dirname)
        self.clone_repo()

    def check_repo(self) -> None:
        """Check input file for Git repository."""
        # Check input file
        if not self.opt["input"].exists():
            return

        self.brewinfo.file = self.opt["input"]

        # Check input file if it points repository or not
        self.opt["repo"] = ""
        with open(self.opt["input"], "r") as f:
            lines = f.readlines()
        for line in lines:
            if re.match(" *git ", line) is None:
                continue
            git_line = line.split()
            if len(git_line) > 1:
                self.opt["repo"] = git_line[1]
                break
        if self.opt["repo"] == "":
            return

        # Check repository name and add git@github.com: if necessary
        if (
            "@" not in self.opt["repo"]
            and not self.opt["repo"].startswith("git://")
            and not self.opt["repo"].startswith("http://")
            and not self.opt["repo"].startswith("file:///")
            and not self.opt["repo"].startswith("/")
        ):
            self.opt["repo"] = (
                "git@github.com:" + self.user_name() + "/" + self.repo_name()
            )

        # Set Brewfile in the repository
        self.brewinfo.file = self.repo_file()

        # If repository does not have a branch, make it
        if self.brewinfo.check_dir():
            self.init_repo()
            return

        # Check and prepare repository
        if "github" in self.opt["repo"]:
            self.check_github_repo()
        elif self.opt["repo"].startswith("file:///") or self.opt[
            "repo"
        ].startswith("/"):
            self.check_local_repo()
        else:
            self.clone_repo()

    def check_gitconfig(self) -> bool:
        if self.opt["repo"].startswith("git://") or self.opt[
            "repo"
        ].startswith("http"):
            self.log.info(
                f"You are using repository of {self.opt['repo']}\n"
                "Use ssh protocol to push your Brewfile update.",
            )
            return False
        _, name = self.helper.proc(
            "git config user.name",
            print_cmd=False,
            print_out=False,
            exit_on_err=False,
            separate_err=True,
        )
        _, email = self.helper.proc(
            "git config user.email",
            print_cmd=False,
            print_out=False,
            exit_on_err=False,
            separate_err=True,
        )
        if not name or not email:
            self.log.warning(
                "You don't have user/email information in your .gitconfig.\n"
                "To commit and push your update, run\n"
                '  git config --global user.email "you@example.com"\n'
                '  git config --global user.name "Your Name"\n'
                "and try again.",
            )
            return False
        return True

    def repomgr(self, cmd: str = "pull") -> None:
        """Helper of repository management."""
        # Check the repository
        if self.opt["repo"] == "":
            raise RuntimeError(
                "Please set a repository, or reset with:\n"
                f"    $ {__prog__} set_repo\n"
            )

        # Clone if it doesn't exist
        if not self.brewinfo.check_dir():
            self.clone_repo()

        # pull/push
        dirname = self.brewinfo.get_dir()

        ret, lines = self.helper.proc(
            "git status -s -uno",
            print_cmd=False,
            print_out=False,
            exit_on_err=True,
            cwd=dirname,
        )
        if ret != 0:
            raise RuntimeError("\n".join(lines))
        if lines:
            if self.check_gitconfig():
                _ = self.helper.proc(
                    "git add -A", dryrun=self.opt["dryrun"], cwd=dirname
                )
                _ = self.helper.proc(
                    ["git", "commit", "-m", '"Update the package list"'],
                    exit_on_err=False,
                    dryrun=self.opt["dryrun"],
                    cwd=dirname,
                )

        _ = self.helper.proc(
            f"git {cmd}", dryrun=self.opt["dryrun"], cwd=dirname
        )

    def brew_cmd(self) -> None:
        noinit = False
        if self.opt["args"] and "noinit" in self.opt["args"]:
            noinit = True
            self.opt["args"].remove("noinit")

        exe = ["brew"]
        cmd = self.opt["args"][0] if self.opt["args"] else ""
        subcmd = self.opt["args"][1] if len(self.opt["args"]) > 1 else ""
        args = self.opt["args"]
        if cmd == "mas":
            exe = ["mas"]
            self.opt["args"].pop(0)
            if subcmd == "uninstall":
                exe = ["sudo", "mas"]
            package = self.opt["args"][1:] if len(self.opt["args"]) > 1 else ""
            if self.check_mas_cmd(True) != 1:
                msg = "\n'mas' command is not available.\n"
                if package:
                    msg += f"Please install 'mas' or manage {' '.join(package)} manually"
                raise RuntimeError(msg)
        if cmd == "whalebrew":
            exe = ["whalebrew"]
            self.opt["args"].pop(0)
            if subcmd == "uninstall":
                self.opt["args"].append("-y")
            if self.check_whalebrew_cmd(True) != 1:
                raise RuntimeError("\n'whalebrew' command is not available.\n")
        if cmd == "code":
            exe = ["code"]
            self.opt["args"].pop(0)
            if self.check_vscode_cmd(True) != 1:
                raise RuntimeError(
                    "\n'code' command (for VSCode) is not available.\n"
                )

        ret, lines = self.helper.proc(
            exe + self.opt["args"],
            print_cmd=False,
            print_out=True,
            exit_on_err=False,
            dryrun=self.opt["dryrun"],
        )
        if self.opt["dryrun"]:
            return

        if (
            noinit
            or (cmd == "mas" and self.opt["appstore"] != 1)
            or (cmd == "whalebrew" and self.opt["whalebrew"] != 1)
            or (cmd == "code" and self.opt["vscode"] != 1)
            or (
                ret != 0
                and "Not installed" not in " ".join(lines)
                and "No installed keg or cask with the name"
                not in " ".join(lines)
            )
        ):
            return

        if cmd in ["cask"]:
            args = self.opt["args"][2:]
        else:
            args = self.opt["args"][1:]
        nargs = len(args)

        if (
            cmd
            not in [
                "instal",
                "install",
                "reinstall",
                "tap",
                "rm",
                "remove",
                "uninstall",
                "untap",
                "cask",
                "mas",
                "whalebrew",
                "code",
            ]
            or nargs == 0
            or (
                cmd == "cask"
                and subcmd
                not in ["instal", "install", "rm", "remove", "uninstall"]
            )
            or (
                cmd == "mas"
                and subcmd not in ["purchase", "install", "uninstall"]
            )
            or (cmd == "whalebrew" and subcmd not in ["install", "uninstall"])
            or (
                cmd == "code"
                and subcmd
                not in ["--install-extension", "--uninstall-extension"]
            )
        ):
            # Not install/remove command, no init.
            return

        _ = self.initialize(check=False, debug_out=True)

    def add_path(self) -> None:
        env_path = os.getenv("PATH", "")
        paths = env_path.split(":")
        for path in [
            "/home/linuxbrew/.linuxbrew/bin",
            os.getenv("HOME", "") + "/.linuxbrew/bin",
            "/opt/homebrew/bin",
            "/usr/local/bin",
        ]:
            if path not in paths:
                os.environ["PATH"] = path + ":" + env_path

    def which_brew(self) -> bool:
        ret, cmd = self.helper.proc(
            "which brew",
            print_cmd=False,
            print_out=False,
            exit_on_err=False,
        )
        if ret == 0:
            self.opt["brew_cmd"] = cmd[0]
            self.opt["is_brew_cmd"] = True
            return True
        return False

    def check_brew_cmd(self) -> bool:
        """Check Homebrew."""
        if self.opt.get("is_brew_cmd", False):
            return True

        if self.which_brew():
            return True

        self.add_path()
        if self.which_brew():
            return True

        self.log.info("Homebrew has not been installed, install now...")
        with tempfile.NamedTemporaryFile() as f:
            cmd = (
                f"curl -o {f.name} -O https://raw.githubusercontent.com/"
                "Homebrew/install/master/install.sh"
            )
            _ = self.helper.proc(
                cmd,
                print_cmd=True,
                print_out=True,
                exit_on_err=False,
            )
            cmd = f"bash {f.name}"
            _ = self.helper.proc(
                cmd,
                print_cmd=True,
                print_out=True,
                exit_on_err=False,
            )
        if not self.which_brew():
            return False
        ret, lines = self.helper.proc(
            "brew doctor",
            print_cmd=True,
            print_out=True,
            exit_on_err=False,
        )
        if ret != 0:
            for line in lines:
                self.log.info(line)
            self.log.warning(
                "\n\nCheck brew environment and fix problems if necessary.\n"
                "# You can check by:\n"
                "#     $ brew doctor",
            )
        return True

    def check_cmd(
        self, flag: str, cmd: str, formula: str, force: bool = False
    ) -> Literal[-2, -1, 0, 1]:
        """Check command is installed or not."""
        if self.opt[flag] != 0:
            return self.opt[flag]

        ret, _ = self.helper.proc(
            f"type {cmd}", print_cmd=False, print_out=False, exit_on_err=False
        )
        if ret != 0:
            self.log.info(f"{formula} has not been installed.")
            if not force:
                ans = self.ask_yn(f"Do you want to install {formula}?")
                if not ans:
                    self.log.warning("If you need it, please do:")
                    self.log.warning(f"    $ brew install {formula}")
                    self.opt[flag] = -2
                    return self.opt[flag]
            ret, _ = self.helper.proc(
                ["brew", "install", formula],
                print_cmd=True,
                print_out=True,
                exit_on_err=False,
            )
            if ret != 0:
                self.log.error(f"\nFailed to install {formula}\n")
                self.opt[flag] = -1
                return self.opt[flag]
            p = Path(formula).name
            if p not in self.get_list("brew_list"):
                self.brewinfo.brew_list.append(p)
                self.brewinfo.brew_list_opt[p] = ""

        ret, _ = self.helper.proc(
            f"type {cmd}", print_cmd=False, print_out=False, exit_on_err=False
        )
        if ret != 0:
            raise RuntimeError(f"Failed to prepare {cmd} command.")

        self.opt[flag] = 1
        return self.opt[flag]

    def check_mas_cmd(self, force: bool = False) -> Literal[-2, -1, 0, 1]:
        """Check mas is installed or not."""
        if self.opt["is_mas_cmd"] != 0:
            return self.opt["is_mas_cmd"]

        if not is_mac():
            raise RuntimeError("mas is not available on Linux!")

        _, lines = self.helper.proc(
            "sw_vers -productVersion",
            print_cmd=False,
            print_out=False,
            exit_on_err=False,
        )
        sw_vers = lines[0].split(".")
        if int(sw_vers[0]) < 10 or (
            int(sw_vers[0]) == 10 and int(sw_vers[1]) < 11
        ):
            self.log.warning("You are using older OS X. mas can not be used.")
            self.opt["is_mas_cmd"] = -1
            return self.opt["is_mas_cmd"]

        cmd_ret = self.check_cmd(
            "is_mas_cmd", self.opt["mas_cmd"], self.opt["mas_formula"], force
        )
        if cmd_ret != 1:
            return cmd_ret

        # # Disable check until this issue is solved:
        # # https://github.com/mas-cli/mas#%EF%B8%8F-known-issues
        # if self.helper.proc(self.opt["mas_cmd"] + " account", print_cmd=False,
        #             print_out=False, exit_on_err=False)[0] != 0:
        #    raise RuntimeError("Please sign in to the App Store.")

        is_tmux = os.getenv("TMUX", "")
        if is_tmux != "":
            ret, _ = self.helper.proc(
                "type reattach-to-user-namespace",
                print_cmd=False,
                print_out=False,
                exit_on_err=False,
            )
            if ret != 0:
                if not force:
                    ans = self.ask_yn(
                        f"You need {self.opt['reattach_formula']} in tmux. Do you want to install it?"
                    )
                    if not ans:
                        self.log.warning("If you need it, please do:")
                        self.log.warning(
                            f"    $ brew install {self.opt['reattach_formula']}"
                        )
                        self.opt["is_mas_cmd"] = -2
                        return self.opt["is_mas_cmd"]
                ret, _ = self.helper.proc(
                    ["brew", "install", self.opt["reattach_formula"]],
                    print_cmd=True,
                    print_out=True,
                    exit_on_err=False,
                )
                if ret != 0:
                    self.log.error(
                        "\nFailed to install "
                        + self.opt["reattach_formula"]
                        + "\n"
                    )
                    self.opt["is_mas_cmd"] = -1
                    return self.opt["is_mas_cmd"]
                p = Path(self.opt["reattach_formula"]).name
                if p not in self.get_list("brew_list"):
                    self.brewinfo.brew_list.append(p)
                    self.brewinfo.brew_list_opt[p] = ""
                self.opt["reattach_cmd_installed"] = True
            self.opt["mas_cmd"] = "reattach-to-user-namespace mas"

        return self.opt["is_mas_cmd"]

    def check_whalebrew_cmd(
        self, force: bool = False
    ) -> Literal[-2, -1, 0, 1]:
        """Check whalebrew is installed or not."""
        if self.opt["is_whalebrew_cmd"] != 0:
            return self.opt["is_whalebrew_cmd"]

        return self.check_cmd(
            "is_whalebrew_cmd",
            self.opt["whalebrew_cmd"],
            self.opt["whalebrew_formula"],
            force,
        )

    def check_vscode_cmd(self, force: bool = False) -> Literal[-2, -1, 0, 1]:
        """Check code (for VSCode) is installed or not."""
        if self.opt["is_vscode_cmd"] != 0:
            return self.opt["is_vscode_cmd"]

        return self.check_cmd(
            "is_vscode_cmd",
            self.opt["vscode_cmd"],
            self.opt["vscode_formula"],
            force,
        )

    def check_docker_running(self) -> Literal[-2, -1, 0, 1]:
        """Check if Docker is running."""
        if self.opt["docker_running"] != 0:
            return self.opt["docker_running"]
        ret, _ = self.helper.proc(
            "type docker", print_cmd=False, print_out=False, exit_on_err=False
        )
        if ret != 0:
            self.opt["docker_running"] = -1
            return self.opt["docker_running"]
        ret, _ = self.helper.proc(
            "docker ps",
            print_cmd=False,
            print_out=False,
            exit_on_err=False,
        )
        if ret != 0:
            self.opt["docker_running"] = -2
            return self.opt["docker_running"]
        self.opt["docker_running"] = 1
        return self.opt["docker_running"]

    def get_appstore_dict(self) -> dict[str, list[str]]:
        apps: dict[str, list[str]] = {}
        _, apps_tmp = self.helper.proc(
            "mdfind 'kMDItemAppStoreHasReceipt=1'",
            print_cmd=False,
            print_out=False,
        )
        for a in apps_tmp:
            if not a.endswith(".app"):
                self.log.warning(f"Incorrect app name in mdfind: {a}")
                continue
            if not Path(a).is_dir():
                self.log.warning(f"App doesn't exist: {a}")
                continue
            _, lines = self.helper.proc(
                f"mdls -attr kMDItemAppStoreAdamID -attr kMDItemVersion '{a}'",
                print_cmd=False,
                print_out=False,
            )
            app = {
                x.split("=")[0].strip(): x.split("=")[1].strip() for x in lines
            }
            app_id = app["kMDItemAppStoreAdamID"]
            if app_id != "(null)":
                app_name = a.split("/")[-1].split(".app")[0]
                app_version = app["kMDItemVersion"].strip('"')
                apps[app_name] = [app_id, f"({app_version})"]
        return apps

    def get_appstore_list(self) -> list[str]:
        return [
            f"{v[0]} {k} {v[1]}" for k, v in self.get_appstore_dict().items()
        ]

    def get_whalebrew_list(self) -> list[str]:
        if self.opt["whalebrew"] != 1:
            return []
        if self.check_whalebrew_cmd(False) != 1:
            return []
        _, lines = self.helper.proc(
            f"{self.opt['whalebrew_cmd']} list",
            print_cmd=False,
            print_out=False,
            exit_on_err=False,
        )
        images = [x.split()[1] for x in lines if x.split()[0] != "COMMAND"]
        return images

    def get_vscode_list(self) -> list[str]:
        if self.opt["vscode"] != 1:
            return []
        if self.check_vscode_cmd(False) != 1:
            return []
        _, lines = self.helper.proc(
            f"{self.opt['vscode_cmd']} --list-extensions",
            print_cmd=False,
            print_out=False,
            exit_on_err=False,
        )
        return lines

    def get_installed_packages(
        self, force_appstore_list: bool = False
    ) -> None:
        """Get Installed Package List."""
        # Clear lists
        for bi in self.brewinfo_ext + [self.brewinfo_main]:
            bi.clear_list()

        # Brew packages
        if not self.opt["caskonly"]:
            info = self.helper.get_info()
            full_list = self.helper.get_formula_list()
            self.brewinfo.brew_full_list.extend(full_list)
            if self.opt["leaves"]:
                packages = self.helper.get_leaves(
                    on_request=self.opt["on_request"]
                )
            elif self.opt["on_request"]:
                packages = []
                for p in info:
                    installed = self.helper.get_installed(p, info[p])
                    if installed.get("installed_on_request", True) in [
                        True,
                        None,
                    ]:
                        packages.append(p)

            else:
                packages = copy.deepcopy(full_list)

            for p in self.opt["top_packages"].split(","):
                if p == "":
                    continue
                if p in full_list and p not in packages:
                    packages.append(p)

            for p in packages:
                self.brewinfo.brew_list.append(p)
                self.brewinfo.brew_list_opt[p] = self.helper.get_option(
                    p, info[p]
                )

        # Taps
        _, lines = self.helper.proc(
            "brew tap",
            print_cmd=False,
            print_out=False,
        )

        self.brewinfo.set_list_val("tap_list", lines)
        if self.opt["api"] and self.opt[
            "core_repo"
        ] not in self.brewinfo.get_list("tap_list"):
            self.brewinfo.add_to_list("tap_list", [self.opt["core_repo"]])
        if (
            is_mac()
            and self.opt["api"]
            and self.opt["cask_repo"] not in self.brewinfo.get_list("tap_list")
        ):
            self.brewinfo.add_to_list("tap_list", [self.opt["cask_repo"]])
        self.brewinfo.add_to_list("tap_list", ["direct"])

        # Casks
        if is_mac():
            for p in self.helper.get_cask_list():
                if len(p.split()) == 1:
                    self.brewinfo.cask_list.append(p)
                else:
                    self.log.warning(
                        "The cask file of " + p + " doesn't exist."
                    )
                    self.log.warning("Please check later.\n\n")
                    self.brewinfo.cask_nocask_list.append(p)

        # App Store
        if is_mac():
            if self.opt["appstore"] == 1 or (
                self.opt["appstore"] == 2 and force_appstore_list
            ):
                self.brewinfo.set_list_val(
                    "appstore_list", self.get_appstore_list()
                )
            elif self.opt["appstore"] == 2:
                if self.brewinfo.check_file():
                    self.read_all()
                self.brewinfo.set_list_val(
                    "appstore_list",
                    list(self.get_list("appstore_input")),
                )

        # Whalebrew commands
        if self.opt["whalebrew"]:
            self.brewinfo.set_list_val(
                "whalebrew_list", self.get_whalebrew_list()
            )

        # VSCode extensions
        if self.opt["vscode"]:
            self.brewinfo.set_list_val("vscode_list", self.get_vscode_list())

    def clean_list(self) -> None:
        """Remove duplications between brewinfo.list to extra files' input."""
        # Cleanup extra files
        aliases = self.helper.get_formula_aliases()
        for b in self.brewinfo_ext + [self.brewinfo_main]:
            for line in ["brew", "tap", "cask", "appstore"]:
                for p in b.get_list(line + "_input"):
                    # Keep aliases
                    if line == "brew" and p in aliases:
                        if aliases[p] in self.brewinfo.get_list("brew_list"):
                            self.brewinfo.add_to_list("brew_list", [p])
                            self.brewinfo.add_to_dict(
                                "brew_list_opt",
                                {
                                    p: self.brewinfo.get_dict("brew_list_opt")[
                                        aliases[p]
                                    ]
                                },
                            )
                            self.brewinfo.remove("brew_list", aliases[p])
                            self.brewinfo.remove("brew_list_opt", aliases[p])
                    if p not in self.brewinfo.get_list(line + "_list"):
                        b.remove(line + "_input", p)

        # Copy list to main file
        self.list_to_main()

        # Loop over lists to remove duplications.
        # tap_list is not checked for overlap removal.
        # Keep it in main list in any case.
        for name in ["brew", "cask", "cask_nocask", "appstore"]:
            if name == "cask_nocask":
                i = "cask"
            else:
                i = name
            for p in self.brewinfo_main.get_list(name + "_list"):
                if p in self.get_list(i + "_input", True):
                    self.brewinfo_main.remove(name + "_list", p)

        # Keep mian/file in main Brewfile
        self.brewinfo_main.add_to_list(
            "main_list", self.brewinfo_main.main_input
        )
        self.brewinfo_main.add_to_list(
            "file_list", self.brewinfo_main.file_input
        )

        # Copy input to list for extra files.
        self.input_to_list(only_ext=True)

    def input_backup(self) -> bool:
        if self.opt["backup"] != "":
            os.rename(self.opt["input"], self.opt["backup"])
            self.log.info(f"Old input file was moved to {self.opt['backup']}")
        else:
            ans = self.ask_yn("Do you want to overwrite it?")
            if not ans:
                return False
        return True

    def set_brewfile_local(self) -> None:
        """Set Brewfile to local file."""
        self.opt["repo"] = ""
        _ = self.initialize(check=False, check_input=False)

    def set_brewfile_repo(self) -> bool:
        """Set Brewfile repository."""
        # Check input file
        if self.opt["input"].exists():
            prev_repo = ""
            with open(self.opt["input"], "r") as f:
                lines = f.readlines()
            for line in lines:
                if re.match(" *git ", line) is None:
                    continue
                git_line = line.split()
                if len(git_line) > 1:
                    prev_repo = git_line[1]
                    break
            if self.opt["repo"] == "":
                self.log.info(
                    f"Input file: {self.opt['input']} is already there."
                )
                if prev_repo != "":
                    self.log.info(
                        f"git repository for Brewfile is already set as {prev_repo}."
                    )

            if not self.input_backup():
                return False

        # Get repository
        if self.opt["repo"] == "":
            self.log.info(
                "\nSet repository,\n"
                '"non" (or empty) for local Brewfile '
                f"({self.opt['input']}),\n"
                "/path/to/repo for local git repository,\n"
                "https://your/git/repository "
                "(or ssh://user@server.project.git) for git repository,\n"
                "or (<user>/)<repo> for github repository,"
            )
            self.opt["repo"] = input("or full path for other git repository: ")
            self.banner("# Set Brewfile repository as " + self.opt["repo"])

        if self.opt["repo"] in ["non", ""]:
            self.set_brewfile_local()
        else:
            # Write repository to the input file
            with OpenWrapper(self.opt["input"], "w") as f:
                f.write("git " + self.opt["repo"])
            self.check_repo()
        return True

    def initialize(
        self,
        check: bool = True,
        check_input: bool = True,
        debug_out: bool = False,
    ) -> bool:
        """Initialize Brewfile."""
        if self.opt["initialized"]:
            return True

        if check:
            if not self.opt["input"].exists():
                ans = self.ask_yn(
                    "Do you want to set a repository (y)? "
                    "((n) for local Brewfile)."
                )
                if ans:
                    if not self.set_brewfile_repo():
                        return False
            else:
                if self.opt["repo"] != "":
                    self.log.info(
                        f"You are using Brewfile of {self.opt['repo']}."
                    )
                else:
                    self.log.info(f"{self.opt['input']} is already there.")
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
            f"# You can edit {self.brewinfo.file} with:\n"
            f"#     $ {__prog__} edit",
            debug_out=debug_out,
        )
        self.opt["initialized"] = True

    def check_input_file(self) -> None:
        """Check input file."""
        if not self.brewinfo.check_file():
            self.log.warning(f"Input file {self.brewinfo.file} is not found.")
            ans = self.ask_yn(
                "Do you want to initialize from installed packages?"
            )
            if ans:
                _ = self.initialize(check=False)

            raise RuntimeError(
                "Ok, please prepare brewfile\n"
                "or you can initialize {self.brewinfo.file} with:"
                f"    $ {__prog__} init"
            )

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
            for x in [self.brewinfo_main] + self.brewinfo_ext
            if all_files or x.file.exists()
        ]
        if error_no_file and not files:
            raise RuntimeError(
                "No Brewfile found. Please run `brew file init` first."
            )
        if is_print:
            self.log.info("\n".join([str(x) for x in files]))
        return files

    def edit_brewfile(self) -> None:
        """Edit brewfiles."""
        editor = shlex.split(self.opt["my_editor"])
        subprocess.call(editor + [str(x) for x in self.get_files()])

    def cat_brewfile(self) -> None:
        """Cat brewfiles."""
        subprocess.call(["cat"] + [str(x) for x in self.get_files()])

    def clean_non_request(self) -> None:
        """Clean up non requested packages."""
        info = self.helper.get_info()
        leaves = self.helper.get_leaves()
        for p in info:
            if p not in leaves:
                continue
            installed = self.helper.get_installed(p, info[p])
            if installed.get("installed_on_request", False) is False:
                cmd = "brew uninstall " + p
                _ = self.helper.proc(
                    cmd,
                    print_cmd=False,
                    print_out=True,
                    dryrun=self.opt["dryrun"],
                )

    def cleanup(self, delete_cache: bool = True) -> None:
        """Clean up."""
        # Get installed package list
        self.get_installed_packages()

        # Check up packages in the input file
        self.read_all()
        info = self.helper.get_info()

        def add_dependncies(package: str) -> None:
            for pac in info[package]["dependencies"]:
                p = pac.split("/")[-1]
                if p not in info:
                    continue
                if p not in self.get_list("brew_input"):
                    self.brewinfo.brew_input.append(p)
                    self.brewinfo.brew_input_opt[p] = ""
                    add_dependncies(p)

        for p in self.get_list("brew_input"):
            if p not in info:
                continue
            add_dependncies(p)

        # Clean up Whalebrew images
        if self.opt["whalebrew"] == 1 and self.get_list("whalebrew_list"):
            self.banner("# Clean up Whalebrew images")

            for image in self.get_list("whalebrew_list"):
                if image in self.get_list("whalebrew_input"):
                    continue

                if self.check_mas_cmd(True) == 1:
                    cmd = f"{self.opt['whalebrew_cmd']} uninstall -y {image.split('/')[-1]}"
                    _ = self.helper.proc(
                        cmd,
                        print_cmd=True,
                        print_out=True,
                        exit_on_err=False,
                        dryrun=self.opt["dryrun"],
                    )
                    self.remove_pack("whalebrew_list", image)

        # Clean up VSCode extensions
        if self.opt["vscode"] == 1 and self.get_list("vscode_list"):
            self.banner("# Clean up VSCode extensions")

            for e in self.get_list("vscode_list"):
                if e in self.get_list("vscode_input"):
                    continue

                if self.check_mas_cmd(True) == 1:
                    cmd = f"{self.opt['vscode_cmd']} --uninstall-extension {e}"
                    _ = self.helper.proc(
                        cmd,
                        print_cmd=True,
                        print_out=True,
                        exit_on_err=False,
                        dryrun=self.opt["dryrun"],
                    )
                    self.remove_pack("vscode_list", e)

        # Clean up App Store applications
        if self.opt["appstore"] == 1 and self.get_list("appstore_list"):
            self.banner("# Clean up App Store applications")

            for p in self.get_list("appstore_list"):
                identifier = p.split()[0]
                if identifier.isdigit():
                    package = " ".join(p.split()[1:])
                else:
                    identifier = ""
                    package = p
                if re.match(r".*\(\d+\.\d+.*\)$", package):
                    package = " ".join(package.split(" ")[:-1])

                isinput = False
                for pi in self.get_list("appstore_input"):
                    i_identifier = pi.split()[0]
                    if i_identifier.isdigit():
                        i_package = " ".join(pi.split()[1:])
                    else:
                        i_identifier = ""
                        i_package = pi
                    if re.match(r".*\(\d+\.\d+.*\)$", i_package):
                        i_package = " ".join(i_package.split(" ")[:-1])
                    if (
                        identifier != "" and identifier == i_identifier
                    ) or package == i_package:
                        isinput = True
                        break
                if isinput:
                    continue

                if identifier and self.check_mas_cmd(True) == 1:
                    cmd = (
                        "sudo "
                        + self.opt["mas_cmd"]
                        + " uninstall "
                        + identifier
                    )
                else:
                    ret, _ = self.helper.proc(
                        "type uninstall",
                        print_cmd=False,
                        print_out=False,
                        exit_on_err=False,
                    )
                    if ret == 0:
                        cmd = "sudo uninstall"
                    else:
                        cmd = "sudo rm -rf"
                    tmpcmd = cmd
                    for d in self.opt["appdirlist"]:
                        a = f"{d}/{package}.app"
                        if Path(a).is_dir():
                            if ret == 0:
                                cmd += " file:///" + quote(a)
                            else:
                                cmd += f" '{a}'"
                            continue
                    if cmd == tmpcmd:
                        self.log.warning(
                            f"Package {package} was not found:"
                            "nothing to do.\n"
                        )
                        self.remove_pack("appstore_list", p)
                        continue
                _ = self.helper.proc(
                    cmd,
                    print_cmd=True,
                    print_out=True,
                    exit_on_err=False,
                    dryrun=self.opt["dryrun"],
                )
                self.remove_pack("appstore_list", p)

        # Clean up cask packages
        if is_mac() and self.get_list("cask_list"):
            self.banner("# Clean up cask packages")
            for p in self.get_list("cask_list"):
                if p in self.get_list("cask_input"):
                    continue
                cmd = "brew uninstall " + p
                _ = self.helper.proc(
                    cmd,
                    print_cmd=True,
                    print_out=True,
                    dryrun=self.opt["dryrun"],
                )
                self.remove_pack("cask_list", p)

        # Skip clean up cask at tap if any cask packages exist
        if is_mac() and self.get_list("cask_list"):
            self.remove_pack("tap_list", self.opt["cask_repo"])

        # Clean up brew packages
        if self.get_list("brew_list"):
            self.banner("# Clean up brew packages")
            for p in self.get_list("brew_list"):
                if p in self.get_list("brew_input"):
                    continue
                # Use --ignore-dependencies option to remove packages w/o
                # formula (tap of which could be removed before).
                cmd = "brew uninstall --ignore-dependencies " + p
                _ = self.helper.proc(
                    cmd,
                    print_cmd=False,
                    print_out=True,
                    dryrun=self.opt["dryrun"],
                )

        # Clean up tap packages
        if self.get_list("tap_list"):
            self.banner("# Clean up tap packages")
            for p in self.get_list("tap_list"):
                if p in self.get_list("tap_input"):
                    continue
                untapflag = True
                for tp in self.helper.get_tap_packs(p):
                    if tp in self.get_list("brew_input"):
                        # Keep the Tap as related package is remained
                        untapflag = False
                        break
                if not untapflag:
                    continue
                if is_mac():
                    for tc in self.helper.get_tap_casks(p):
                        if tc in self.get_list("cask_input"):
                            # Keep the Tap as related cask is remained
                            untapflag = False
                            break
                if not untapflag:
                    continue
                cmd = "brew untap " + p
                _ = self.helper.proc(
                    cmd,
                    print_cmd=True,
                    print_out=True,
                    dryrun=self.opt["dryrun"],
                )

        # Clean up cashe
        self.banner("# Clean up cache")
        cmd0 = "brew cleanup"
        _ = self.helper.proc(
            cmd0, print_cmd=True, print_out=True, dryrun=self.opt["dryrun"]
        )
        if delete_cache:
            cmd1 = "rm -rf " + self.helper.brew_val("cache")
            _ = self.helper.proc(
                cmd1, print_cmd=True, print_out=True, dryrun=self.opt["dryrun"]
            )

    def install(self) -> None:
        # Reinit flag
        reinit = 0

        # Get installed package list
        self.get_installed_packages(force_appstore_list=True)

        # Check packages in the input file
        self.read_all()

        # before commands
        for c in self.get_list("before_input"):
            _ = self.helper.proc(c, dryrun=self.opt["dryrun"])

        # Tap
        for p in self.get_list("tap_input"):
            if p in self.get_list("tap_list") or p == "direct":
                continue
            _ = self.helper.proc("brew tap " + p, dryrun=self.opt["dryrun"])

        # Cask
        if is_mac():
            cask_args_opt = {"--cask": "", "--force": ""}
            cask_args_opt.update(self.get_dict("cask_args_input"))

            for p in self.get_list("cask_input"):
                if p in self.get_list("cask_list"):
                    continue
                cask_args = {}
                cask_args.update(cask_args_opt)
                args = []
                for k, v in cask_args.items():
                    args.append(k)
                    if v != "":
                        args.append(v)
                _ = self.helper.proc(
                    f"brew install {shlex.join(args)} {p}",
                    dryrun=self.opt["dryrun"],
                )

        # brew
        if not self.opt["caskonly"]:
            # Brew
            aliases = self.helper.get_formula_aliases()
            for p in self.get_list("brew_input"):
                cmd = "install"
                pack = aliases[p] if p in aliases else p
                if pack in self.get_list("brew_full_list"):
                    if p not in self.get_dict("brew_list_opt") or sorted(
                        self.get_dict("brew_input_opt")[p].split()
                    ) == sorted(self.get_dict("brew_list_opt")[p].split()):
                        continue
                    # Uninstall to install the package with new options
                    # `reinstall` does not accept options such a --HEAD.
                    _ = self.helper.proc(
                        "brew uninstall " + p, dryrun=self.opt["dryrun"]
                    )
                ret, lines = self.helper.proc(
                    "brew "
                    + cmd
                    + " "
                    + p
                    + self.get_dict("brew_input_opt")[p],
                    dryrun=self.opt["dryrun"],
                )
                if ret != 0:
                    self.log.warning(
                        "Can not install " + p + "."
                        "Please check the package name.\n"
                        f"{p} may be installed "
                        "by using web direct formula.",
                    )
                    continue
                for line in lines:
                    if line.find("ln -s") != -1:
                        if self.opt["link"]:
                            cmdtmp = line.split()
                            cmd_ln = []
                            for c in cmdtmp:
                                cmd_ln.append(str(expandpath(c)))
                            _ = self.helper.proc(cmd_ln)
                    if line.find("brew linkapps") != -1:
                        if self.opt["link"]:
                            _ = self.helper.proc("brew linkapps")
                if (
                    p in self.get_list("brew_list")
                    and self.get_dict("brew_input_opt")[p]
                    != self.get_dict("brew_list_opt")[p]
                ):
                    self.brewinfo.add_to_dict(
                        "brew_input_opt", {p: self.helper.get_option(p)}
                    )
                    reinit = 1

        # App Store
        if is_mac() and self.opt["appstore"]:
            id_list = [x.split()[0] for x in self.get_list("appstore_list")]
            for p in self.get_list("appstore_input"):
                identifier = p.split()[0]
                if identifier in id_list:
                    continue
                if identifier.isdigit() and len(identifier) >= 9:
                    package = " ".join(p.split()[1:])
                else:
                    identifier = ""
                    package = p
                islist = False
                for pl in self.get_list("appstore_list"):
                    l_identifier = pl.split()[0]
                    if l_identifier.isdigit() and len(l_identifier) >= 9:
                        l_package = " ".join(pl.split()[1:])
                    else:
                        l_identifier = ""
                        l_package = pl
                    if package == l_package:
                        islist = True
                        break
                if islist:
                    continue
                self.log.info(f"Installing {package}")
                if identifier != "":
                    if self.opt["dryrun"] or self.check_mas_cmd(True) == 1:
                        _ = self.helper.proc(
                            self.opt["mas_cmd"] + " install " + identifier,
                            dryrun=self.opt["dryrun"],
                        )
                    else:
                        self.log.info(
                            f"Please install {package} from AppStore."
                        )
                        _ = self.helper.proc(
                            f"open -W 'macappstore://itunes.apple.com/app/id{identifier}'",
                            dryrun=self.opt["dryrun"],
                        )
                else:
                    self.log.warning(
                        "No id or wrong id information was given for "
                        f"AppStore App: {package}.\n"
                        "Please install it manually.",
                    )

        # Whalebrew commands
        if self.opt["whalebrew"]:
            images = self.get_list("whalebrew_list")
            for image in self.get_list("whalebrew_input"):
                if image in images:
                    continue
                self.log.info(f"Installing {image}")
                if self.opt["dryrun"] or self.check_whalebrew_cmd(True) == 1:
                    if not self.opt[
                        "dryrun"
                    ] and self.check_docker_running() in [-1, -2]:
                        if self.check_docker_running() == -1:
                            self.log.warning(
                                "Docker command is not available."
                            )
                        elif self.check_docker_running() == -2:
                            self.log.warning("Docker is not running.")
                        self.log.warning(
                            f"Please install {image} by whalebrew after docker is ready."
                        )
                        continue
                    _ = self.helper.proc(
                        self.opt["whalebrew_cmd"] + " install " + image,
                        dryrun=self.opt["dryrun"],
                    )
                else:
                    self.log.warning(f"Please install {image} by whalebrew.")

        # VSCode extensions
        if self.opt["vscode"]:
            extensions = self.get_list("vscode_list")
            for e in self.get_list("vscode_input"):
                if e in extensions:
                    continue
                self.log.info(f"Installing {e}")
                if self.opt["dryrun"] or self.check_vscode_cmd(True) == 1:
                    _ = self.helper.proc(
                        self.opt["vscode_cmd"] + " --install-extension " + e,
                        dryrun=self.opt["dryrun"],
                    )
                else:
                    self.log.warning(f"Please install {e} to VSCode.")

        # Other commands
        for c in self.get_list("cmd_input"):
            _ = self.helper.proc(c, dryrun=self.opt["dryrun"])

        # after commands
        for c in self.get_list("after_input"):
            _ = self.helper.proc(c, dryrun=self.opt["dryrun"])

        # Initialize if commands are installed
        if reinit or max(
            [
                self.opt[f"{x}_cmd_installed"]
                for x in ["mas", "reattach", "whalebrew", "vscode"]
            ]
        ):
            self.opt["mas_cmd_installed"] = self.opt[
                "reattach_cmd_installed"
            ] = self.opt["whalebrew_cmd_installed"] = self.opt[
                "vscode_cmd_installed"
            ] = False
            self.input_to_list()
            self.initialize_write(debug_out=True)

    def generate_cask_token(self, app: str) -> str:
        # Ref: https://github.com/Homebrew/homebrew-cask/blob/c24db49e9489190949096156a1f97ee02c15c68b/developer/bin/generate_cask_token#L267
        token = app.split("/")[-1]
        if token.endswith(".app"):
            token = token[:-4]
        token = token.replace("+", "plus")
        token = token.replace("@", "at")
        token = token.replace(" ", "-").lower()
        token = re.sub(r"[^a-z0-9-]", "", token)
        token = re.sub(r"-+", "-", token)
        token = re.sub(r"^-+", "", token)
        token = re.sub(r"-([0-9])", "\\g<1>", token)
        return token

    def make_brew_app_cmd(self, name: str, app_path: str) -> str:
        return f"brew {name} # {app_path}"

    def make_cask_app_cmd(self, name: str, app_path: str) -> str:
        return f"cask {name} # {app_path}"

    def make_appstore_app_cmd(self, name: str, app_path: str) -> str:
        return f"appstore {name} # {app_path}"

    def check_cask(self) -> None:
        """Check applications for Cask."""
        if not is_mac():
            raise RuntimeError("Cask is not available on Linux!")

        self.banner("# Starting to check applications for Cask...")

        # First, get App Store applications
        appstore_list = self.get_appstore_dict()

        # Check installed casks untill brew info --eval-all contains core/cask for AMI
        # once fixed, compare info['token']['version'] and installed to check latest
        cask_list = self.helper.get_cask_list()

        # Get cask information
        info = self.helper.get_cask_info()
        casks: dict[str, dict[str, str | bool]] = {}
        apps: dict[str, str] = {}
        installed_casks: dict[str, list[str]] = {self.opt["cask_repo"]: []}
        for cask_info in info:
            apps_in_cask = []
            # installed = True if cask_info["installed"] is not None else False
            installed = cask_info["token"] in cask_list
            latest = False
            if installed:
                if cask_info["installed"] is None:
                    # No AMI info by --eval-all, using json, which does not have installed information
                    # In addition, some AMI casks (e.g. firefox, zoom) can not work with brew info.
                    latest = True
                else:
                    latest = cask_info["installed"] == cask_info["version"]
                installed_casks[cask_info["tap"]] = installed_casks.get(
                    cask_info["tap"], []
                ) + [cask_info["token"]]

            if "artifacts" in cask_info:
                for artifact in cask_info["artifacts"]:
                    if "app" in artifact:
                        for a in artifact["app"]:
                            if isinstance(a, str):
                                apps_in_cask.append(a)
                    if "uninstall" in artifact:
                        for uninstall in artifact["uninstall"]:
                            if "delete" in uninstall:
                                for a in uninstall["delete"]:
                                    if isinstance(a, str) and a.endswith(
                                        ".app"
                                    ):
                                        apps_in_cask.append(a)
            casks[cask_info["token"]] = {
                "tap": cask_info["tap"],
                "installed": installed,
                "latest": latest,
            }
            apps_in_cask = list(set(apps_in_cask))
            for a in apps_in_cask:
                if a not in apps or installed:
                    apps[a] = cask_info["token"]
        # brew
        formulae = self.helper.get_formula_list()
        brews = {
            x["name"]: {"tap": x["tap"], "installed": x["name"] in formulae}
            for x in self.helper.get_formula_info()
        }

        # Set applications directories
        app_dirs = self.opt["appdirlist"]
        apps_check = {
            "cask": dict.fromkeys(app_dirs, 0),
            "has_cask": dict.fromkeys(app_dirs, 0),
            "brew": dict.fromkeys(app_dirs, 0),
            "has_brew": dict.fromkeys(app_dirs, 0),
            "appstore": dict.fromkeys(app_dirs, 0),
            "no_cask": dict.fromkeys(app_dirs, 0),
        }

        appstore_apps: dict[str, str] = {}
        appstore_has_cask_apps: CaskInfo = {}
        cask_apps: CaskListInfo = {self.opt["cask_repo"]: []}
        non_latest_cask_apps: CaskListInfo = {self.opt["cask_repo"]: []}
        has_cask_apps: CaskListInfo = {self.opt["cask_repo"]: []}
        brew_apps: CaskListInfo = {self.opt["core_repo"]: []}
        has_brew_apps: CaskListInfo = {self.opt["core_repo"]: []}
        no_cask: list[str] = []

        # Get applications
        napps = 0
        for d in app_dirs:
            for app in sorted(
                [
                    a
                    for a in os.listdir(d)
                    if not a.startswith(".")
                    and a != "Utilities"
                    and Path(d + "/" + a).is_dir()
                ]
            ):
                check = "no_cask"
                app_path = home_tilde(f"{d}/{app}")
                aname = app
                if aname.endswith(".app"):
                    aname = aname[:-4]
                if app in apps:
                    token = apps[app]
                elif app_path in apps:
                    token = apps[app_path]
                else:
                    token = self.generate_cask_token(app)

                if aname in appstore_list:
                    check = "appstore"
                    name = (
                        appstore_list[aname][0]
                        + " "
                        + aname
                        + " "
                        + appstore_list[aname][1]
                    )
                    if token in casks:
                        appstore_has_cask_apps[name] = (token, app_path)
                    else:
                        appstore_apps[name] = app_path
                else:
                    if token in casks:
                        cask_tap = cast(str, casks[token]["tap"])
                        if casks[token]["installed"]:
                            check = "cask"
                            if casks[token]["latest"]:
                                cask_apps[cask_tap] = cask_apps.get(
                                    cask_tap, []
                                ) + [(app_path, token)]
                            else:
                                non_latest_cask_apps[cask_tap] = (
                                    non_latest_cask_apps.get(cask_tap, [])
                                    + [(app_path, token)]
                                )
                            if token in installed_casks[cask_tap]:
                                installed_casks[cask_tap].remove(token)
                        else:
                            check = "has_cask"
                            has_cask_apps[cask_tap] = has_cask_apps.get(
                                cask_tap, []
                            ) + [(app_path, token)]
                    elif token in brews:
                        brew_tap = cast(str, brews[token]["tap"])
                        if brews[token]["installed"]:
                            check = "brew"
                            brew_apps[brew_tap] = brew_apps.get(
                                brew_tap, []
                            ) + [(app_path, token)]
                        else:
                            check = "has_brew"
                            has_brew_apps[brew_tap] = has_brew_apps.get(
                                brew_tap, []
                            ) + [(app_path, token)]
                if check == "no_cask":
                    no_cask.append(app_path)
                apps_check[check][d] += 1
                napps += 1

        # Make list
        casks_in_others = []
        output = ""

        output += "# Cask applications\n\n"

        for tap in set(cask_apps.keys()) or set(has_cask_apps.keys()):
            output += f"# Apps installed by cask in {tap}\n"
            if tap != self.opt["cask_repo"] or not self.opt["api"]:
                output += f"tap {tap}\n"
            for app_path, token in sorted(cask_apps[tap], key=lambda x: x[1]):
                if token not in casks_in_others:
                    output += self.make_cask_app_cmd(token, app_path) + "\n"
                    casks_in_others.append(token)
                else:
                    output += f"#{self.make_cask_app_cmd(token, app_path)}\n"
            output += "\n"

            if tap in non_latest_cask_apps and non_latest_cask_apps[tap]:
                output += "# New version are available for following apps\n"
                for app_path, token in sorted(non_latest_cask_apps[tap]):
                    if token not in casks_in_others:
                        output += (
                            self.make_cask_app_cmd(token, app_path) + "\n"
                        )
                        casks_in_others.append(token)
                    else:
                        output += (
                            f"#{self.make_cask_app_cmd(token, app_path)}\n"
                        )
                output += "\n"

            if tap in installed_casks and installed_casks[tap]:
                output += (
                    "# Cask is found, but no applications are found "
                    + "(could be fonts, system settings, "
                    + "or installed in other directory.)\n"
                )
                for token in sorted(installed_casks[tap]):
                    if token not in casks_in_others:
                        output += f"cask {token}\n"
                        casks_in_others.append(token)
                    else:
                        output += f"#cask {token}\n"
                output += "\n"

            if tap in has_cask_apps and has_cask_apps[tap]:
                output += "# Apps installed directly instead of by cask\n"
                for app_path, token in sorted(has_cask_apps[tap]):
                    output += f"#{self.make_cask_app_cmd(token, app_path)}\n"
                output += "\n"

        for tap in set(brew_apps.keys()) or set(has_brew_apps.keys()):
            output += f"# Apps installed by brew in {tap}\n"
            if tap != self.opt["core_repo"] or not self.opt["api"]:
                output += f"tap {tap}\n"
            for app_path, token in sorted(brew_apps[tap], key=lambda x: x[1]):
                if token not in casks_in_others:
                    output += self.make_brew_app_cmd(token, app_path) + "\n"
                    casks_in_others.append(token)
                else:
                    output += f"#{self.make_brew_app_cmd(token, app_path)}\n"
            output += "\n"

            if tap in has_brew_apps and has_brew_apps[tap]:
                output += "# Apps installed directly instead of by brew\n"
                for app_path, token in sorted(has_brew_apps[tap]):
                    output += f"#{self.make_brew_app_cmd(token, app_path)}\n"
                output += "\n"

        if appstore_apps:
            output += "# Apps installed from AppStore\n"
            for name, app_path in appstore_apps.items():
                output += self.make_appstore_app_cmd(name, app_path) + "\n"
            output += "\n"

        if appstore_has_cask_apps:
            output += (
                "# Apps installed from AppStore, but casks are available.\n"
            )
            for name, (token, app_path) in appstore_has_cask_apps.items():
                output += (
                    self.make_appstore_app_cmd(name, f"{token}, {app_path}")
                    + "\n"
                )
            output += "\n"

        if no_cask:
            output += "# Apps installed but no casks are available\n"
            output += "# (System applications or directory installed.)\n"
            for app_path in no_cask:
                output += f"# {app_path}\n"

        with open("Caskfile", "w") as f:
            f.write(output)
        self.log.debug(output)

        # Summary
        self.banner("# Summary")
        self.log.info(
            f"Total:{napps} apps have been checked.\n"
            f"Apps in {[home_tilde(d) for d in app_dirs]}\n"
        )
        maxlen = max(len(home_tilde(x)) for x in app_dirs)
        if sum(apps_check["cask"].values()) > 0:
            self.log.info("Installed by Cask:")
            for d in app_dirs:
                if apps_check["cask"][d] == 0:
                    continue
                self.log.info(
                    f"{home_tilde(d):{maxlen}s} : {apps_check['cask'][d]}"
                )
            self.log.info("")
        if sum(apps_check["brew"].values()) > 0:
            self.log.info("Installed by brew install command")
            for d in app_dirs:
                if apps_check["brew"][d] == 0:
                    continue
                self.log.info(
                    f"{home_tilde(d):{maxlen}s} : {apps_check['brew'][d]}"
                )
            self.log.info("")
        if sum(apps_check["has_cask"].values()) > 0:
            self.log.info("Installed directly, but casks are available:")
            for d in app_dirs:
                if apps_check["has_cask"][d] == 0:
                    continue
                self.log.info(
                    f"{home_tilde(d):{maxlen}s} : {apps_check['has_cask'][d]}"
                )
            self.log.info("")
        if sum(apps_check["appstore"].values()) > 0:
            self.log.info("Installed from Appstore")
            for d in app_dirs:
                if apps_check["appstore"][d] == 0:
                    continue
                self.log.info(
                    f"{home_tilde(d):{maxlen}s} : {apps_check['appstore'][d]}"
                )
            self.log.info("")
        if sum(apps_check["no_cask"].values()) > 0:
            self.log.info("No casks")
            for d in app_dirs:
                if apps_check["no_cask"][d] == 0:
                    continue
                self.log.info(
                    f"{home_tilde(d):{maxlen}s} : {apps_check['no_cask'][d]}"
                )
            self.log.info("")

    def execute(self) -> None:
        """Main execute function."""
        # Cask list check
        if self.opt["command"] == "casklist":
            self.check_cask()
            return

        # Set BREWFILE repository
        if self.opt["command"] == "set_repo":
            _ = self.set_brewfile_repo()
            return

        # Set BREWFILE to local file
        if self.opt["command"] == "set_local":
            self.set_brewfile_local()
            return

        # Change brewfile if it is repository's one or not.
        self.check_repo()

        # Do pull/push for the repository.
        if self.opt["command"] in ["pull", "push"]:
            with self.DryrunBanner(self):
                self.repomgr(self.opt["command"])
            return

        # brew command
        if self.opt["command"] == "brew":
            with self.DryrunBanner(self):
                self.brew_cmd()
            return

        # Initialize
        if self.opt["command"] in ["init", "dump"]:
            _ = self.initialize()
            return

        # Edit
        if self.opt["command"] == "edit":
            self.edit_brewfile()
            return

        # Cat
        if self.opt["command"] == "cat":
            self.cat_brewfile()
            return

        # Get files
        if self.opt["command"] == "get_files":
            self.get_files(is_print=True, all_files=self.opt["all_files"])
            return

        # Check input file
        # If the file doesn't exist, initialize it.
        self.check_input_file()

        # Cleanup non request
        if self.opt["command"] == "clean_non_request":
            with self.DryrunBanner(self):
                self.clean_non_request()
            return

        # Cleanup
        if self.opt["command"] == "clean":
            with self.DryrunBanner(self):
                self.cleanup()
            return

        # Install
        if self.opt["command"] == "install":
            with self.DryrunBanner(self):
                self.install()
            return

        # Update
        if self.opt["command"] == "update":
            with self.DryrunBanner(self):
                if not self.opt["noupgradeatupdate"]:
                    _ = self.helper.proc(
                        "brew update", dryrun=self.opt["dryrun"]
                    )
                    fetch_head = (
                        "--fetch-HEAD" if self.opt["fetch_head"] else ""
                    )
                    _ = self.helper.proc(
                        f"brew upgrade --formula {fetch_head}",
                        dryrun=self.opt["dryrun"],
                    )
                    if is_mac():
                        _ = self.helper.proc(
                            "brew upgrade --cask", dryrun=self.opt["dryrun"]
                        )
                if self.opt["repo"] != "":
                    self.repomgr("pull")
                self.install()
                self.cleanup(delete_cache=False)
                if not self.opt["dryrun"]:
                    _ = self.initialize(check=False, debug_out=True)
                if self.opt["repo"] != "":
                    self.repomgr("push")
            return

        # No command found
        raise RuntimeError(
            f"Wrong command: {self.opt['command']}\n"
            f"Execute `{__prog__} help` for more information."
        )
