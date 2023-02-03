import copy
import glob
import logging
import os
import re
import shlex
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import quote

from .brew_helper import BrewHelper
from .brew_info import BrewInfo
from .info import __prog__
from .utils import OpenWrapper, StrRe, Tee, expandpath, is_mac, to_bool, to_num


@dataclass
class BrewFile:
    """Main class of Brew-file."""

    opt: dict = field(default_factory=dict)

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

        self.set_input(self.opt["input"])

        self.pack_deps: dict[str, list[str]] = {}
        self.top_packs: list[str] = []

        self.editor = ""

        # fix up opt
        self.set_args()

    def default_opt(self) -> dict[str, Any]:
        opt: dict[str, Any] = {}
        opt["verbose"] = os.environ.get("HOMEBREW_BREWFILE_VERBOSE", "info")
        opt["command"] = ""
        opt["input"] = Path(os.environ.get("HOMEBREW_BREWFILE", ""))
        if not opt["input"].name:
            brewfile_config = (
                Path(
                    os.environ.get(
                        "XDG_CONFIG_HOME", os.environ["HOME"] + "/.config"
                    ),
                )
                / "brewfile/Brewfile"
            )
            brewfile_home = Path(os.environ["HOME"] + "/.brewfile/Brewfile")
            if not brewfile_config.is_file() and brewfile_home.is_file():
                opt["input"] = brewfile_home
            else:
                opt["input"] = brewfile_config
        opt["backup"] = os.environ.get("HOMEBREW_BREWFILE_BACKUP", "")
        opt["form"] = None
        opt["leaves"] = to_bool(
            os.environ.get("HOMEBREW_BREWFILE_LEAVES", False)
        )
        opt["on_request"] = to_bool(
            os.environ.get("HOMEBREW_BREWFILE_ON_REQUEST", False)
        )
        opt["top_packages"] = os.environ.get(
            "HOMEBREW_BREWFILE_TOP_PACKAGES", ""
        )
        opt["repo"] = ""
        opt["noupgradeatupdate"] = False
        opt["link"] = True
        opt["caskonly"] = False
        opt["dryrun"] = False
        opt["initialized"] = False
        opt["cask_repo"] = "homebrew/cask"
        opt["reattach_formula"] = "reattach-to-user-namespace"
        opt["mas_formula"] = "mas"
        opt["my_editor"] = os.environ.get(
            "HOMEBREW_BREWFILE_EDITOR", os.environ.get("EDITOR", "vim")
        )
        opt["brew_cmd"] = ""
        opt["mas_cmd"] = "mas"
        opt["is_mas_cmd"] = 0
        opt["mas_cmd_installed"] = False
        opt["reattach_cmd_installed"] = False
        opt["args"] = []
        opt["yn"] = False
        opt["brew_packages"] = ""
        opt["homebrew_ruby"] = False

        # Check Homebrew variables
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

        opt["appstore"] = to_num(
            os.environ.get("HOMEBREW_BREWFILE_APPSTORE", -1)
        )
        opt["no_appstore"] = False

        opt["all_files"] = False
        opt["read"] = False

        return opt

    def set_input(self, file: str | Path) -> None:
        self.opt["input"] = Path(file)
        self.brewinfo = BrewInfo(self.helper, self.opt["input"])
        self.brewinfo_ext: list[BrewInfo] = []
        self.brewinfo_main = self.brewinfo

    def debug_banner(self) -> None:
        if self.opt["dryrun"]:
            self.banner("# This is dry run.")

    def parse_env_opts(
        self, env_var: str, base_opts: dict | None = None
    ) -> dict:
        """Returns a dictionary parsed from an environment variable."""
        if base_opts is not None:
            opts = base_opts.copy()
        else:
            opts = {}

        env_var = env_var.upper()
        env_opts = os.environ.get(env_var, None)
        if env_opts:

            # these can be flags ("--flag") or values ("--key=value")
            # but not weirdness ("--foo=bar=baz")
            user_opts = {
                key.lower(): value
                for (key, value) in [
                    pair.partition("=")[::2]
                    for pair in env_opts.split()
                    if pair.count("=") < 2
                ]
            }

            if user_opts:
                opts.update(user_opts)
            else:
                self.log.warning(
                    '{env_var}: "{env_opts}" is not a proper format.'
                )
                self.log.warning("Ignoring the value.\n")

        return opts

    def set_verbose(self, verbose: str | None = None) -> None:
        if verbose is None:
            self.opt["verbose"] = os.environ.get(
                "HOMEBREW_BREWFILE_VERBOSE", "info"
            )
        # Keep compatibility with old verbose
        match self.opt["verbose"]:
            case "0":
                self.opt["verbose"] = "debug"
            case "1":
                self.opt["verbose"] = "info"
            case "2":
                self.opt["verbose"] = "error"

        if self.log.parent:
            self.log.parent.setLevel(
                getattr(logging, self.opt["verbose"].upper())
            )
        else:
            self.log.setLevel(getattr(logging, self.opt["verbose"].upper()))

    def set_args(self, **kw) -> None:
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

        self.brewinfo.file = self.opt["input"]

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

    def banner(self, text: str) -> None:
        self.helper.banner(text)

    def read_all(self, force=False):
        if not force and self.opt["read"]:
            return
        self.brewinfo_ext = [self.brewinfo]
        self.brewinfo_main = self.read(self.brewinfo, is_main=True)
        self.brewinfo_ext.remove(self.brewinfo_main)
        if self.opt["mas_cmd_installed"]:
            p = Path(self.opt["mas_formula"]).name
            if p not in self.get("brew_input"):
                self.brewinfo_main.brew_input.append(p)
                self.brewinfo_main.brew_input_opt[p] = ""
        if self.opt["reattach_cmd_installed"]:
            p = Path(self.opt["reattach_formula"]).name
            if p not in self.get("brew_input"):
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

    def list_to_main(self):
        if self.brewinfo == self.brewinfo_main:
            return
        self.brewinfo_main.add("brew_list", self.brewinfo.brew_list)
        self.brewinfo_main.add("brew_full_list", self.brewinfo.brew_list)
        self.brewinfo_main.add("tap_list", self.brewinfo.tap_list)
        self.brewinfo_main.add("cask_list", self.brewinfo.cask_list)
        self.brewinfo_main.add(
            "cask_nocask_list", self.brewinfo.cask_nocask_list
        )
        self.brewinfo_main.add("appstore_list", self.brewinfo.appstore_list)
        self.brewinfo_main.add("brew_list_opt", self.brewinfo.brew_list_opt)

    def input_to_list(self, only_ext=False):
        if not only_ext:
            self.brewinfo_main.input_to_list()
        for b in self.brewinfo_ext:
            b.input_to_list()

    def write(self):
        self.banner(f"# Initialize {self.brewinfo_main.file}")
        self.brewinfo_main.write()
        for b in self.brewinfo_ext:
            self.banner(f"# Initialize {b.file}")
            b.write()

    def get(self, name, only_ext=False) -> set | dict:
        list_copy = self.brewinfo_main.get(name)
        if isinstance(list_copy, list):
            if only_ext:
                del list_copy[:]
            for b in self.brewinfo_ext:
                list_copy += b.get(name)
            return set(list_copy)
        elif isinstance(list_copy, dict):
            if only_ext:
                list_copy.clear()
            for b in self.brewinfo_ext:
                list_copy.update(b.get(name))
            return list_copy

    def remove_pack(self, name, package):
        if package in self.brewinfo_main.get(name):
            self.brewinfo_main.remove(name, package)
        else:
            for b in self.brewinfo_ext:
                if package in b.get(name):
                    b.remove(name, package)

    def repo_name(self):
        return self.opt["repo"].split("/")[-1].split(".git")[0]

    def user_name(self):
        user = ""
        repo_split = self.opt["repo"].split("/")
        if len(repo_split) > 1:
            user = repo_split[-2].split(":")[-1]
        if not user:
            user = self.helper.proc(
                "git config --get github.user",
                print_cmd=False,
                print_out=False,
                exit_on_err=False,
                separate_err=False,
            )[1]
            if user:
                user = user[0]
            else:
                user = self.helper.proc(
                    "git config --get user.name",
                    print_cmd=False,
                    print_out=False,
                    exit_on_err=False,
                    separate_err=False,
                )[1]
                if user:
                    user = user[0]
                else:
                    user = ""
            if user == "":
                raise RuntimeError("Can not find git (github) user name")
        return user

    def input_dir(self):
        return self.opt["input"].parent

    def input_file(self):
        return self.opt["input"].name

    def repo_file(self) -> Path:
        """Helper to build Brewfile path for the repository."""
        return Path(
            self.input_dir(),
            self.user_name() + "_" + self.repo_name(),
            self.input_file(),
        )

    def init_repo(self):
        dirname = self.brewinfo.get_dir()
        os.chdir(dirname)
        branches = self.helper.proc(
            "git branch",
            print_cmd=False,
            print_out=False,
            exit_on_err=True,
            separate_err=True,
        )[1]
        if branches:
            return

        self.log.info("Initialize the repository with README.md/Brewfile.")
        if not Path("README.md").exists():
            f = open("README.md", "w")
            f.write(
                "# " + self.repo_name() + "\n\n"
                "Package list for [homebrew](http://brew.sh/).\n\n"
                "Managed by "
                "[homebrew-file](https://github.com/rcmdnk/homebrew-file)."
            )
            f.close()
        self.brewinfo.file.touch()

        if self.check_gitconfig():
            self.helper.proc("git add -A")
            self.helper.proc(
                ["git", "commit", "-m", '"Prepared by ' + __prog__ + '"']
            )
            self.helper.proc("git push -u origin master")

    def clone_repo(self, exit_on_err=True):
        ret = self.helper.proc(
            "git clone "
            + self.opt["repo"]
            + ' "'
            + self.brewinfo.get_dir()
            + '"',
            print_cmd=True,
            print_out=True,
            exit_on_err=False,
        )[0]
        if ret != 0:
            if exit_on_err:
                self.err(
                    0,
                )
                raise RuntimeError(
                    f"Can not clone {self.opt['repo']}.\n"
                    "please check the repository, or reset with\n"
                    f"    $ {__prog__} set_repo"
                )
            else:
                return False
        self.init_repo()
        return True

    def check_github_repo(self):
        """Helper to check and create GitHub repository."""
        # Check if the repository already exists or not.
        if self.clone_repo(exit_on_err=False):
            return

        # Create new repository #
        raise RuntimeError(
            f"GitHub repository: {self.user_name()}/{self.repo_name()} doesn't exist.\n"
            "Please create the repository first, then try again"
        )

    def check_local_repo(self):
        dirname = self.opt["repo"].replace("file:///", "")
        if not Path(dirname).is_dir():
            os.makedirs(dirname)
        os.chdir(dirname)
        self.helper.proc("git init --bare")
        self.clone_repo()

    def check_repo(self):
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

    def check_gitconfig(self):
        if self.opt["repo"].startswith("git://") or self.opt[
            "repo"
        ].startswith("http"):
            self.log.info(
                f"You are using repository of {self.opt['repo']}\n"
                "Use ssh protocol to push your Brewfile update.",
            )
            return False
        name = self.helper.proc(
            "git config user.name",
            print_cmd=False,
            print_out=False,
            exit_on_err=False,
            separate_err=True,
        )[1]
        email = self.helper.proc(
            "git config user.email",
            print_cmd=False,
            print_out=False,
            exit_on_err=False,
            separate_err=True,
        )[1]
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

    def repomgr(self, cmd="pull"):
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
        self.log.info(f"$ cd {self.brewinfo.get_dir()}")
        os.chdir(self.brewinfo.get_dir())

        ret, lines = self.helper.proc(
            "git status -s -uno",
            print_cmd=False,
            print_out=False,
            exit_on_err=True,
        )
        if ret != 0:
            raise RuntimeError("\n".join(lines))
        if lines:
            if self.check_gitconfig():
                self.helper.proc("git add -A", dryrun=self.opt["dryrun"])
                self.helper.proc(
                    ["git", "commit", "-m", '"Update the package list"'],
                    exit_on_err=False,
                    dryrun=self.opt["dryrun"],
                )

        self.helper.proc(f"git {cmd}", dryrun=self.opt["dryrun"])

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
                self.log.error("\n'mas' command is not available.\n")
                if package:
                    self.log.error(
                        "Please install 'mas' or "
                        f"{subcmd} {' '.join(package)} manually",
                        0,
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
            or (
                cmd == "mas"
                and subcmd != "uninstall"
                and self.opt["appstore"] != 1
            )
        ) or (
            ret != 0
            and "Not installed" not in " ".join(lines)
            and "No installed keg or cask with the name" not in " ".join(lines)
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
        ):
            # Not install/remove command, no init.
            return

        _ = self.initialize(check=False)

    def add_path(self):
        paths = os.environ["PATH"].split(":")
        for path in [
            "/home/linuxbrew/.linuxbrew/bin",
            os.environ["HOME"] + "/.linuxbrew/bin",
            "/opt/homebrew/bin",
            "/usr/local/bin",
        ]:
            if path not in paths:
                os.environ["PATH"] = path + ":" + os.environ["PATH"]

    def which_brew(self):
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

    def check_brew_cmd(self):
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
            self.helper.proc(
                cmd,
                print_cmd=True,
                print_out=True,
                exit_on_err=False,
            )
            cmd = f"bash {f.name}"
            self.helper.proc(
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

    def check_mas_cmd(self, force=False):
        """Check mas is installed or not."""
        if self.opt["is_mas_cmd"] != 0:
            return self.opt["is_mas_cmd"]

        if not is_mac():
            raise RuntimeError("mas is not available on Linux!")

        if (
            self.helper.proc(
                "type mas", print_cmd=False, print_out=False, exit_on_err=False
            )[0]
            != 0
        ):
            sw_vers = self.helper.proc(
                "sw_vers -productVersion",
                print_cmd=False,
                print_out=False,
                exit_on_err=False,
            )[1][0].split(".")
            if int(sw_vers[0]) < 10 or (
                int(sw_vers[0]) == 10 and int(sw_vers[1]) < 11
            ):
                self.log.warning("You are using older OS X. mas is not used.")
                self.opt["is_mas_cmd"] = -1
                return self.opt["is_mas_cmd"]
            self.log.info(f"{self.opt['mas_formula']} has not been installed.")
            if not force:
                ans = self.ask_yn(
                    "Do you want to install {self.opt['mas_formula']}?"
                )
                if not ans:
                    self.log.warning("If you need it, please do:")
                    self.log.warning(
                        "    $ brew install {self.opt['mas_formula']}"
                    )
                    self.opt["is_mas_cmd"] = -2
                    return self.opt["is_mas_cmd"]
            ret = self.helper.proc(
                ["brew", "install", self.opt["mas_formula"]],
                print_cmd=True,
                print_out=True,
                exit_on_err=False,
            )[0]
            if ret != 0:
                self.err(
                    "\nFailed to install " + self.opt["mas_formula"] + "\n", 0
                )
                self.opt["is_mas_cmd"] = -1
                return self.opt["is_mas_cmd"]
            p = Path(self.opt["mas_formula"]).name
            if p not in self.get("brew_list"):
                self.brewinfo.brew_list.append(p)
                self.brewinfo.brew_list_opt[p] = ""

        if (
            self.helper.proc(
                self.opt["mas_cmd"],
                print_cmd=False,
                print_out=False,
                exit_on_err=False,
            )[0]
            != 0
        ):
            raise RuntimeError("Failed to prepare mas command.")

        # Disable check until this issue is solved:
        # https://github.com/mas-cli/mas#%EF%B8%8F-known-issues
        # if self.helper.proc(self.opt["mas_cmd"] + " account", print_cmd=False,
        #             print_out=False, exit_on_err=False)[0] != 0:
        #    raise RuntimeError("Please sign in to the App Store.")

        self.opt["is_mas_cmd"] = 1

        is_tmux = os.environ.get("TMUX", "")
        if is_tmux != "":
            if (
                self.helper.proc(
                    "type reattach-to-user-namespace",
                    print_cmd=False,
                    print_out=False,
                    exit_on_err=False,
                )[0]
                != 0
            ):
                if not force:
                    ans = self.ask_yn(
                        f"You need {self.opt['reattach_formula']} in tmux. Do you want to install it?"
                    )
                    if not ans:
                        self.log.warning("If you need it, please do:")
                        self.log.warning(
                            f"    $ brew install {self.opt['reattach_formula']}"
                        )
                        return self.opt["is_mas_cmd"]
                ret = self.helper.proc(
                    ["brew", "install", self.opt["reattach_formula"]],
                    print_cmd=True,
                    print_out=True,
                    exit_on_err=False,
                )[0]
                if ret != 0:
                    self.err(
                        "\nFailed to install "
                        + self.opt["reattach_formula"]
                        + "\n",
                        0,
                    )
                    self.opt["is_mas_cmd"] = -1
                    return self.opt["is_mas_cmd"]
                p = Path(self.opt["reattach_formula"]).name
                if p not in self.get("brew_list"):
                    self.brewinfo.brew_list.append(p)
                    self.brewinfo.brew_list_opt[p] = ""
                self.opt["reattach_cmd_installed"] = True
            self.opt["mas_cmd"] = "reattach-to-user-namespace mas"

        return self.opt["is_mas_cmd"]

    def get_appstore_list(self):
        """Get AppStore Application List."""
        apps = []

        if self.check_mas_cmd(True) == 1:
            lines = self.helper.proc(
                self.opt["mas_cmd"] + " list",
                print_cmd=False,
                print_out=False,
                separate_err=True,
            )[1]
            apps = sorted(lines, key=lambda x: " ".join(x.split()[1:]).lower())
            if apps and apps[0] == "No installed apps found":
                apps = []
        else:
            apps_tmp = []
            for d in self.opt["appdirlist"]:
                apps_tmp += [
                    ("/".join(x.split("/")[:-3]).split(".app")[0])
                    for x in glob.glob(d + "/*/Contents/_MASReceipt/receipt")
                ]
            # Another method
            # Sometime it can not find applications which have not been used?
            # (ret, app_tmp) = self.helper.proc(
            #     "mdfind 'kMDItemAppStoreHasReceipt=1'", print_cmd=False,
            #     print_out=False)
            for a in apps_tmp:
                apps_id = self.helper.proc(
                    f"mdls -name kMDItemAppStoreAdamID -raw '{a}.app'",
                    print_cmd=False,
                    print_out=False,
                )[1][0]
                apps.append(f"{apps_id} {a.split('/')[-1].split('.app')[0]}")

        return apps

    def get_cask_list(self):
        """Get Cask List."""
        lines = self.helper.proc(
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
        return (True, packages)

    def get_list(self, force_appstore_list=False):
        """Get Installed Package List."""
        # Clear lists
        self.brewinfo.clear_list()

        # Brew packages
        if not self.opt["caskonly"]:
            info = self.brewinfo.get_info()
            full_list = self.helper.proc(
                "brew list --formula", print_cmd=False, print_out=False
            )[1]
            del self.brewinfo.brew_full_list[:]
            self.brewinfo.brew_full_list.extend(full_list)
            if self.opt["on_request"]:
                leaves = []
                for p in info:
                    installed = self.brewinfo.get_installed(p, info[p])
                    if (
                        installed["installed_on_request"] is True
                        or installed["installed_on_request"] is None
                    ):
                        leaves.append(p)

            elif self.opt["leaves"]:
                leaves = self.brewinfo.get_leaves()
            else:
                leaves = copy.deepcopy(full_list)

            for p in self.opt["top_packages"].split(","):
                if p == "":
                    continue
                if p in full_list and p not in leaves:
                    leaves.append(p)

            for p in info:
                if p not in leaves:
                    continue
                self.brewinfo.brew_list.append(p)
                self.brewinfo.brew_list_opt[p] = self.brewinfo.get_option(
                    p, info[p]
                )

        # Taps
        lines = self.helper.proc(
            "brew tap",
            print_cmd=False,
            print_out=False,
            env={"HOMEBREW_NO_AUTO_UPDATE": "1"},
        )[1]

        self.brewinfo.set_val("tap_list", lines)
        self.brewinfo.add("tap_list", ["direct"])

        # Casks
        if is_mac():
            for p in self.get_cask_list()[1]:
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
                self.brewinfo.set_val(
                    "appstore_list", self.get_appstore_list()
                )
            elif self.opt["appstore"] == 2:
                if self.brewinfo.check_file():
                    self.read_all()
                self.brewinfo.set_val(
                    "appstore_list", self.get("appstore_input")
                )

    def clean_list(self):
        """Remove duplications between brewinfo.list to extra files' input."""
        # Cleanup extra files
        for b in self.brewinfo_ext + [self.brewinfo_main]:
            for line in ["brew", "tap", "cask", "appstore"]:
                for p in b.get(line + "_input"):
                    if p not in self.brewinfo.get(line + "_list"):
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
            for p in self.brewinfo_main.get(name + "_list"):
                if p in self.get(i + "_input", True):
                    self.brewinfo_main.remove(name + "_list", p)

        # Keep mian/file in main Brewfile
        self.brewinfo_main.add("main_list", self.brewinfo_main.main_input)
        self.brewinfo_main.add("file_list", self.brewinfo_main.file_input)

        # Copy input to list for extra files.
        self.input_to_list(only_ext=True)

    def input_backup(self):
        if self.opt["backup"] != "":
            os.rename(self.opt["input"], self.opt["backup"])
            self.log.info(f"Old input file was moved to {self.opt['backup']}")
        else:
            ans = self.ask_yn("Do you want to overwrite it?")
            if not ans:
                return False
        return True

    def set_brewfile_local(self):
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

    def initialize(self, check=True, check_input=True) -> bool:
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
        self.get_list()

        # Read inputs
        if check_input:
            if self.brewinfo.check_file():
                self.read_all()

            # Remove duplications between brewinfo.list to extra files' input
            self.clean_list()

        # write out
        self.initialize_write()

        return True

    def initialize_write(self):
        self.write()
        self.banner(
            f"# You can edit {self.brewinfo.file} with:\n"
            f"#     $ {__prog__} edit"
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
                f"    $ { __prog__} init"
            )

    def get_files(self, is_print=False, all_files=False):
        """Get Brewfiles."""
        self.read_all()
        files = [
            x.file
            for x in [self.brewinfo_main] + self.brewinfo_ext
            if all_files or x.file.exists()
        ]
        if is_print:
            self.log.info("\n".join(files))
        return files

    def edit_brewfile(self):
        """Edit brewfiles."""
        if not self.editor:
            self.editor = shlex.split(self.opt["my_editor"])
        subprocess.call(self.editor + self.get_files())

    def cat_brewfile(self):
        """Cat brewfiles."""
        subprocess.call(["cat"] + self.get_files())

    def clean_non_request(self):
        """Clean up non requested packages."""
        info = self.brewinfo.get_info()
        leaves = self.brewinfo.get_leaves()
        for p in info:
            if p not in leaves:
                continue
            installed = self.brewinfo.get_installed(p, info[p])
            if installed["installed_on_request"] is False:
                cmd = "brew uninstall " + p
                self.helper.proc(
                    cmd,
                    print_cmd=False,
                    print_out=True,
                    dryrun=self.opt["dryrun"],
                )

    def cleanup(self):
        """Clean up."""
        # Get installed package list
        self.get_list()

        # Check up packages in the input file
        self.read_all()
        info = self.brewinfo.get_info()

        def add_dependncies(package):
            for pac in info[package]["dependencies"]:
                p = pac.split("/")[-1]
                if p not in info:
                    continue
                if p not in self.get("brew_input"):
                    self.brewinfo.brew_input.append(p)
                    self.brewinfo.brew_input_opt[p] = ""
                    add_dependncies(p)

        for p in self.get("brew_input"):
            if p not in info:
                continue
            add_dependncies(p)

        # Clean up App Store applications
        if self.opt["appstore"] == 1 and self.get("appstore_list"):
            self.banner("# Clean up App Store applications")

            for p in self.get("appstore_list"):
                identifier = p.split()[0]
                if identifier.isdigit():
                    package = " ".join(p.split()[1:])
                else:
                    identifier = ""
                    package = p
                if re.match(r".*\(\d+\.\d+.*\)$", package):
                    package = " ".join(package.split(" ")[:-1])

                isinput = False
                for pi in self.get("appstore_input"):
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
                    uninstall = self.helper.proc(
                        "type uninstall",
                        print_cmd=False,
                        print_out=False,
                        exit_on_err=False,
                    )
                    if uninstall == 0:
                        cmd = "sudo uninstall"
                    else:
                        cmd = "sudo rm -rf"
                    tmpcmd = cmd
                    for d in self.opt["appdirlist"]:
                        a = f"{d}/{package}.app"
                        if Path(a).is_dir():
                            if uninstall == 0:
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
                self.helper.proc(
                    cmd,
                    print_cmd=True,
                    print_out=True,
                    exit_on_err=False,
                    dryrun=self.opt["dryrun"],
                )
                self.remove_pack("appstore_list", p)

        # Clean up cask packages
        if is_mac() and self.get("cask_list"):
            self.banner("# Clean up cask packages")
            for p in self.get("cask_list"):
                if p in self.get("cask_input"):
                    continue
                cmd = "brew uninstall " + p
                self.helper.proc(
                    cmd,
                    print_cmd=True,
                    print_out=True,
                    dryrun=self.opt["dryrun"],
                )
                self.remove_pack("cask_list", p)

        # Skip clean up cask at tap if any cask packages exist
        if is_mac() and self.get("cask_list"):
            self.remove_pack("tap_list", self.opt["cask_repo"])

        # Clean up brew packages
        if self.get("brew_list"):
            self.banner("# Clean up brew packages")
            for p in self.get("brew_list"):
                if p in self.get("brew_input"):
                    continue
                # Use --ignore-dependencies option to remove packages w/o
                # formula (tap of which could be removed before).
                cmd = "brew uninstall --ignore-dependencies " + p
                self.helper.proc(
                    cmd,
                    print_cmd=False,
                    print_out=True,
                    dryrun=self.opt["dryrun"],
                )

        # Clean up tap packages
        if self.get("tap_list"):
            self.banner("# Clean up tap packages")
            for p in self.get("tap_list"):
                if p in self.get("tap_input"):
                    continue
                untapflag = True
                for tp in self.brewinfo.get_tap_packs(p):
                    if tp in self.get("brew_input"):
                        # Keep the Tap as related package is remained
                        untapflag = False
                        break
                if not untapflag:
                    continue
                if is_mac():
                    for tc in self.brewinfo.get_tap_casks(p):
                        if tc in self.get("cask_input"):
                            # Keep the Tap as related cask is remained
                            untapflag = False
                            break
                if not untapflag:
                    continue
                cmd = "brew untap " + p
                self.helper.proc(
                    cmd,
                    print_cmd=True,
                    print_out=True,
                    dryrun=self.opt["dryrun"],
                )

        # Clean up cashe
        self.banner("# Clean up cache")
        cmd0 = "brew cleanup"
        cmd1 = "rm -rf " + self.helper.brew_val("cache")
        self.helper.proc(
            cmd0, print_cmd=True, print_out=True, dryrun=self.opt["dryrun"]
        )
        self.helper.proc(
            cmd1, print_cmd=True, print_out=True, dryrun=self.opt["dryrun"]
        )

    def install(self):
        # Reinit flag
        reinit = 0

        # Get installed package list
        self.get_list(force_appstore_list=True)

        # Check packages in the input file
        self.read_all()

        # before commands
        for c in self.get("before_input"):
            self.helper.proc(c, dryrun=self.opt["dryrun"])

        # Tap
        for p in self.get("tap_input"):
            if p in self.get("tap_list") or p == "direct":
                continue
            self.helper.proc("brew tap " + p, dryrun=self.opt["dryrun"])

        # Cask
        if is_mac():
            cask_args_opt = {"--cask": "", "--force": ""}
            for c in self.get("cask_args_input"):
                cask_args_opt.update(c)

            for p in self.get("cask_input"):
                if p in self.get("cask_list"):
                    continue
                cask_args = {}
                cask_args.update(cask_args_opt)
                args = []
                for k, v in cask_args.items():
                    args.append(k)
                    if v != "":
                        args.append(v)
                args = shlex.join(args)
                self.helper.proc(
                    f"brew install {args} {p}", dryrun=self.opt["dryrun"]
                )

        # brew
        if not self.opt["caskonly"]:
            # Brew
            for p in self.get("brew_input"):
                cmd = "install"
                if p in self.get("brew_full_list"):
                    if p not in self.get("brew_list_opt") or sorted(
                        self.get("brew_input_opt")[p].split()
                    ) == sorted(self.get("brew_list_opt")[p].split()):
                        continue
                    # Uninstall to install the package with new options
                    # `reinstall` does not accept options such a --HEAD.
                    self.helper.proc(
                        "brew uninstall " + p, dryrun=self.opt["dryrun"]
                    )
                ret, lines = self.helper.proc(
                    "brew " + cmd + " " + p + self.get("brew_input_opt")[p],
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
                            cmd = []
                            for c in cmdtmp:
                                cmd.append(str(expandpath(c)))
                            self.helper.proc(cmd)
                    if line.find("brew linkapps") != -1:
                        if self.opt["link"]:
                            self.helper.proc("brew linkapps")
                if (
                    p in self.get("brew_list")
                    and self.get("brew_input_opt")[p]
                    != self.get("brew_list_opt")[p]
                ):
                    self.brewinfo.add(
                        "brew_input_opt", {p: self.brewinfo.get_option(p)}
                    )
                    reinit = 1

        # App Store
        if is_mac() and self.opt["appstore"]:
            id_list = [x.split()[0] for x in self.get("appstore_list")]
            for p in self.get("appstore_input"):
                identifier = p.split()[0]
                if identifier in id_list:
                    continue
                if identifier.isdigit() and len(identifier) >= 9:
                    package = " ".join(p.split()[1:])
                else:
                    identifier = ""
                    package = p
                islist = False
                for pl in self.get("appstore_list"):
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
                        self.helper.proc(
                            self.opt["mas_cmd"] + " install " + identifier,
                            dryrun=self.opt["dryrun"],
                        )
                    else:
                        self.log.info(
                            f"Please install {package} from AppStore."
                        )
                        self.helper.proc(
                            f"open -W 'macappstore://itunes.apple.com/app/id{identifier}'",
                            dryrun=self.opt["dryrun"],
                        )
                else:
                    self.log.warning(
                        "No id or wrong id information was given for "
                        f"AppStore App: {package}.\n"
                        "Please install it manually.",
                    )

        # Other commands
        for c in self.get("cmd_input"):
            self.helper.proc(c, dryrun=self.opt["dryrun"])

        # after commands
        for c in self.get("after_input"):
            self.helper.proc(c, dryrun=self.opt["dryrun"])

        # Initialize if commands are installed
        if (
            self.opt["mas_cmd_installed"]
            or self.opt["reattach_cmd_installed"]
            or reinit
        ):
            self.opt["mas_cmd_installed"] = self.opt["reattach_cmd_installed"]
            self.input_to_list()
            self.initialize_write()

    def find_app(
        self, app, taps, casks, nonapp_casks, casks_noinst, nonapp_casks_noinst
    ):
        """Helper function for Cask."""
        cask_namer = (
            self.brewinfo.get_tap_path(self.opt["cask_repo"])
            / "developer/bin/generate_cask_token"
        )
        tap_cands = []
        name_cands = []
        lines = self.helper.proc(
            [str(cask_namer), f"\"{app.split('/')[-1].lower()}\""],
            print_cmd=False,
            print_out=False,
            exit_on_err=False,
        )[1]
        for line in lines:
            if line.find("Proposed token") != -1:
                name_cands.append(line.split()[2])
            if line.find("already exists") != -1:
                for t in taps:
                    tname = t.split("/")[0] + "/homebrew-" + t.split("/")[1]
                    if line.split("'")[1].find(tname) != -1:
                        tap_cands.append(t)
                        break
        if not tap_cands:
            del name_cands[:]

        installed = False
        clist = (
            list(casks.values())
            + nonapp_casks
            + [x for x_list in casks_noinst.values() for x in x_list]
            + nonapp_casks_noinst
        )
        if name_cands and [x for x in clist if x[0] == name_cands[0] and x[2]]:
            installed = True
        else:
            for c in [x for x in clist if app in x[5]]:
                if c[2]:
                    installed = True
                    tap_cands = [c[1]]
                    name_cands = [c[0]]
                    break
                if c[0] not in name_cands:
                    tap_cands.append(c[1])
                    name_cands.append(c[0])
        if not name_cands:
            self.log.debug(f"Non Cask app: {app}")
        elif installed:
            self.log.debug(f"Installed by Cask: {app}{name_cands[0]}")
        else:
            self.log.debug(
                f"Installed directly, instead of by Cask: {app} , Cask candidates: {', '.join(name_cands)}"
            )
        return (tap_cands, installed, name_cands)

    def find_brew_app(self, name, tap):
        """Helper function for Cask to find app installed by brew install."""
        check = "has_cask"
        tap_brew = tap
        opt = ""
        if Path(
            self.helper.brew_val("repository")
            + "/Library/Formula/"
            + name
            + ".rb"
        ).is_file():
            if isinstance(self.opt["brew_packages"], str):
                self.opt["brew_packages"] = self.helper.proc(
                    "brew list --formula", print_cmd=False, print_out=False
                )[1]
            if name in self.opt["brew_packages"]:
                check = "brew"
                opt = self.brewinfo.get_option(name)
                if Path(
                    self.helper.brew_val("repository")
                    + "/Library/Formula/"
                    + name
                    + ".rb"
                ).is_symlink():
                    link = os.readlink(
                        self.helper.brew_val("repository")
                        + "/Library/Formula/"
                        + name
                        + ".rb"
                    )
                    tap_brew = (
                        link.replace("../Taps/", "")
                        .replace("homebrew-")
                        .replace("/" + name + ".rb")
                    )
                else:
                    tap_brew = ""
        return (check, tap_brew, opt)

    def check_cask(self):
        """Check applications for Cask."""
        if not is_mac():
            raise RuntimeError("Cask is not available on Linux!")

        self.banner("# Starting to check applications for Cask...")

        # First, get App Store applications
        appstore_list = {}
        for p in self.get_appstore_list():
            pinfo = p.split()
            identifier = pinfo[0]
            if identifier.isdigit() and len(identifier) == 9:
                package = " ".join(pinfo[1:])
            else:
                identifier = ""
                package = p
            (pname, version) = package.split("(")
            appstore_list[pname.strip()] = [identifier, "(" + version]

        # Get cask list, force to install brew-cask
        # if it has not been installed.
        installed_casks = self.get_cask_list()[1]

        # Set cask directories and reset application information list
        taps = list(
            filter(
                lambda t: (self.brewinfo.get_tap_path(t) / "Casks").is_dir(),
                self.helper.proc(
                    "brew tap",
                    print_cmd=False,
                    print_out=False,
                    env={"HOMEBREW_NO_AUTO_UPDATE": "1"},
                )[1],
            )
        )
        apps = {d: {True: [], False: []} for d in taps + ["", "appstore"]}
        brew_apps = {}

        # Set applications directories
        app_dirs = self.opt["appdirlist"]
        apps_check = {
            "cask": {d: 0 for d in app_dirs},
            "has_cask": {d: 0 for d in app_dirs},
            "brew": {d: 0 for d in app_dirs},
            "appstore": {d: 0 for d in app_dirs},
            "no_cask": {d: 0 for d in app_dirs},
        }

        # Load casks
        casks = {}
        nonapp_casks = []
        casks_noinst = {}
        nonapp_casks_noinst = []
        for t in taps:
            d = Path(self.brewinfo.get_tap_path(t)) / "Casks"
            for cask in [x.stem for x in d.iterdir() if x.suffix == ".rb"]:
                cask_apps = []
                installed = False
                noinst = True
                if cask in installed_casks:
                    noinst = False
                with open((d / cask).with_suffix(".rb"), "r") as f:
                    content = f.read()
                for line in content.split("\n"):
                    cask_app = ""
                    match StrRe(line):
                        case "^ *name ":
                            cask_app = (
                                re.sub("^ *name ", "", line).strip("\"' ")
                                + ".app"
                            )
                        case "^ *app ":
                            cask_app = (
                                re.sub("^ *app ", "", line)
                                .strip("\"' ")
                                .split("/")[-1]
                            )
                        case "\\.app":
                            cask_app = (
                                line.split(".app")[0]
                                .split("/")[-1]
                                .split("'")[-1]
                                .split('"')[-1]
                            )
                        case "^ *pkg ", line:
                            cask_app = (
                                re.sub("^ *pkg ", "", line)
                                .strip("\"' ")
                                .split("/")[-1]
                                .replace(".pkg", "")
                            )
                    if cask_app != "" and cask_app not in cask_apps:
                        cask_apps.append(cask_app)

                    if not noinst and re.search("^ *version ", line):
                        if Path(
                            self.opt["caskroom"]
                            + "/"
                            + cask
                            + "/"
                            + re.sub("^ *version ", "", line).strip("\"': ")
                        ).is_dir():
                            installed = True
                if noinst:
                    if not cask_apps:
                        nonapp_casks_noinst.append(
                            [cask, t, installed, False, content, cask_apps]
                        )
                    else:
                        for a in cask_apps:
                            if a in casks_noinst:
                                casks_noinst[a].append(
                                    [
                                        cask,
                                        t,
                                        installed,
                                        False,
                                        content,
                                        cask_apps,
                                    ]
                                )
                            else:
                                casks_noinst[a] = [
                                    [
                                        cask,
                                        t,
                                        installed,
                                        False,
                                        content,
                                        cask_apps,
                                    ]
                                ]
                else:
                    if not cask_apps:
                        nonapp_casks.append(
                            [cask, t, installed, False, content, cask_apps]
                        )
                    else:
                        for a in cask_apps:
                            casks[a] = [
                                cask,
                                t,
                                installed,
                                False,
                                content,
                                cask_apps,
                            ]

        # Get applications
        napps = 0
        for d in app_dirs:
            for app in [
                x
                for x in os.listdir(d)
                if not x.startswith(".")
                and x != "Utilities"
                and Path(d + "/" + x).is_dir()
            ]:
                check = "no_cask"
                tap = ""
                opt = ""
                aname = app.replace(".app", "")
                if aname in appstore_list:
                    tap = "appstore"
                    installed = False
                    if appstore_list[aname][0] != "":
                        name = (
                            appstore_list[aname][0]
                            + " "
                            + aname
                            + " "
                            + appstore_list[aname][1]
                        )
                    else:
                        name = ""
                    check = "appstore"
                elif app in casks or app.split(".")[0] in casks:
                    app_key = app if app in casks else app.split(".")[0]
                    tap = casks[app_key][1]
                    installed = casks[app_key][2]
                    name = casks[app_key][0]
                    for a in filter(lambda k, n=name: casks[k][0] == n, casks):
                        casks[a][3] = True
                    casks[app_key][3] = True
                    if installed or name != "":
                        installed = True
                        check = "cask"
                else:
                    app_find = app
                    if not app.endswith(".app"):
                        app_find = d + "/" + app
                    (tap_cands, installed, name_cands) = self.find_app(
                        app_find,
                        taps,
                        casks,
                        nonapp_casks,
                        casks_noinst,
                        nonapp_casks_noinst,
                    )
                    if name_cands:
                        for name in name_cands:
                            for c in filter(
                                lambda x, n=name: x[0] == n, nonapp_casks
                            ):
                                nonapp_casks.remove(c)
                            for a in filter(
                                lambda k, n=name: casks[k][0] == n, casks
                            ):
                                casks[a][3] = True
                    name = ""
                    if installed:
                        check = "cask"
                        name = name_cands[0]
                        tap = tap_cands[0]
                    elif name_cands:
                        for n, t in zip(name_cands, tap_cands):
                            (check, tap, opt) = self.find_brew_app(n, t)
                            if check == "brew":
                                name = n
                                break
                    if name == "":
                        if tap_cands:
                            for n, t in zip(name_cands, tap_cands):
                                apps[t][installed].append(
                                    (n, d + "/" + app, check)
                                )
                        else:
                            name = tap = ""
                if check != "has_cask":
                    if check != "brew":
                        apps[tap][installed].append(
                            (name, d + "/" + app, check)
                        )
                    else:
                        if tap not in brew_apps:
                            brew_apps[tap] = []
                        brew_apps[tap].append((name, d + "/" + app, opt))
                apps_check[check][d] += 1
                napps += 1

        # Make list
        casks_in_others = []
        out = Tee(Path("Caskfile"), self.log)

        out.writeln("# Cask applications")
        out.writeln(
            "# Please copy these lines to your Brewfile"
            " and use with `" + __prog__ + " install`.\n"
        )

        out.writeln("# Main tap repository for " + self.opt["cask_repo"])
        out.writeln("tap " + self.opt["cask_repo"])
        out.writeln("")
        if apps[self.opt["cask_repo"]][True]:
            out.writeln("# Apps installed by Cask in " + self.opt["cask_repo"])
            for name, app_path, _ in sorted(apps[self.opt["cask_repo"]][True]):
                if name not in casks_in_others:
                    out.writeln(
                        "cask "
                        + name
                        + " # "
                        + app_path.replace(os.environ["HOME"], "~")
                    )
                    casks_in_others.append(name)
                else:
                    out.writeln(
                        "#cask "
                        + name
                        + " # "
                        + app_path.replace(os.environ["HOME"], "~")
                    )

            out.writeln("")

        if [
            x[0]
            for x in list(casks.values()) + nonapp_casks
            if x[1] == self.opt["cask_repo"] and not x[3]
        ]:
            out.writeln(
                "# Cask is found, but no applications are found "
                + "(could be fonts, system settins, "
                + "or installed in other directory.)"
            )
            for name in sorted(
                x[0]
                for x in list(casks.values()) + nonapp_casks
                if x[1] == self.opt["cask_repo"] and x[2] and not x[3]
            ):
                if name not in casks_in_others:
                    out.writeln("cask " + name)
                    casks_in_others.append(name)
            if [
                x[0]
                for x in list(casks.values()) + nonapp_casks
                if x[1] == self.opt["cask_repo"] and not x[2] and not x[3]
            ]:
                out.writeln(
                    "\n# There are new version for following applications."
                )
                for name in sorted(
                    x[0]
                    for x in list(casks.values()) + nonapp_casks
                    if x[1] == self.opt["cask_repo"] and not x[2] and not x[3]
                ):
                    if name not in casks_in_others:
                        out.writeln("cask install " + name)
                        casks_in_others.append(name)
            out.writeln("")

        if apps[self.opt["cask_repo"]][False]:
            out.writeln(
                "# Apps installed directly instead of by Cask in "
                + self.opt["cask_repo"]
            )
            for name, app_path, _ in sorted(
                x for x in apps[self.opt["cask_repo"]][False]
            ):
                out.writeln(
                    "#cask "
                    + name
                    + " # "
                    + app_path.replace(os.environ["HOME"], "~")
                )
            out.writeln("")

        for t in filter(
            lambda x: x not in (self.opt["cask_repo"], "", "appstore"), taps
        ):
            out.writeln("# Casks in " + t)
            out.writeln("tap " + t)
            out.writeln("")
            if apps[t][True]:
                out.writeln("# Apps installed by Cask in " + t)
                for name, app_path, _ in sorted(apps[t][True]):
                    if name not in casks_in_others:
                        out.writeln(
                            "cask "
                            + name
                            + " # "
                            + app_path.replace(os.environ["HOME"], "~")
                        )
                        casks_in_others.append(name)
                    else:
                        out.writeln(
                            "#cask "
                            + name
                            + " # "
                            + app_path.replace(os.environ["HOME"], "~")
                        )

                out.writeln("")

            if [
                x[0]
                for x in list(casks.values()) + nonapp_casks
                if x[1] == t and not x[3]
            ]:
                out.writeln(
                    "# Cask is found, but no applications are found.\n"
                    "# (fonts, system settins, "
                    "or installed in other directory.)"
                )
                for name in sorted(
                    x[0]
                    for x in list(casks.values()) + nonapp_casks
                    if x[1] == t and x[2] and not x[3]
                ):
                    if name not in casks_in_others:
                        out.writeln("cask " + name)
                        casks_in_others.append(name)
                if [
                    x[0]
                    for x in list(casks.values()) + nonapp_casks
                    if x[1] == t and not x[2] and not x[3]
                ]:
                    out.writeln(
                        "# There are new version for following applications."
                    )
                    for name in sorted(
                        x[0]
                        for x in list(casks.values()) + nonapp_casks
                        if x[1] == t and not x[2] and not x[3]
                    ):
                        if name not in casks_in_others:
                            out.writeln("cask " + name)
                            casks_in_others.append(name)
                out.writeln("")

            if apps[t][False]:
                out.writeln(
                    "# Apps installed directly instead of by Cask in " + t
                )
                for name, app_path, _ in apps[t][False]:
                    out.writeln(
                        "#cask "
                        + name
                        + " # "
                        + app_path.replace(os.environ["HOME"], "~")
                    )
                out.writeln("")

        if brew_apps:
            out.writeln("# Apps installed by brew install command")
            if "" in brew_apps:
                for (name, app_path, opt) in brew_apps[""]:
                    out.writeln(
                        "brew "
                        + name
                        + " "
                        + opt
                        + " # "
                        + app_path.replace(os.environ["HOME"], "~")
                    )
            for tap in [x for x in brew_apps if x != ""]:
                out.writeln("tap " + tap)
                for (name, app_path, opt) in brew_apps[tap]:
                    out.writeln(
                        "brew "
                        + name
                        + " "
                        + opt
                        + " # "
                        + app_path.replace(os.environ["HOME"], "~")
                    )
            out.writeln("")

        if apps["appstore"][False]:
            out.writeln("# Apps installed from AppStore")
            apps_list = ", ".join(
                [
                    " ".join(x[0].split()[1:]).lower()
                    for x in apps["appstore"][False]
                ]
            )
            self.log.debug(f"Apps installed from AppStore: {apps_list}")
            for name, app_path, _ in sorted(
                apps["appstore"][False],
                key=lambda x: " ".join(x[0].split()[1:]).lower(),
            ):
                if name != "":
                    out.writeln("appstore " + name + " # " + app_path)
                else:
                    out.writeln("#appstore # " + app_path)
            out.writeln("")

        if apps[""][False]:
            out.writeln("# Apps installed but no casks are available")
            out.writeln("# (System applications or directory installed.)")
            for _, app_path, _ in apps[""][False]:
                out.writeln("# " + app_path)

        out.close()

        # Summary
        self.banner("# Summary")
        self.log.info(
            f"Total:{napps} apps have been checked.\n"
            f"Apps in {[d.replace(os.environ['HOME'], '~') for d in app_dirs]}\n"
        )
        maxlen = max(len(x.replace(os.environ["HOME"], "~")) for x in app_dirs)
        if sum(apps_check["cask"].values()) > 0:
            self.log.info("Installed by Cask:")
            for d in app_dirs:
                if apps_check["cask"][d] == 0:
                    continue
                self.log.info(
                    f"{d.replace(os.environ['HOME'], '~'):{maxlen}s} : {apps_check['cask'][d]}"
                )
            self.log.info("")
        if sum(apps_check["brew"].values()) > 0:
            self.log.info("Installed by brew install command")
            for d in app_dirs:
                if apps_check["brew"][d] == 0:
                    continue
                self.log.info(
                    f"{d.replace(os.environ['HOME'], '~'):{maxlen}s} : {apps_check['brew'][d]}"
                )
            self.log.info("")
        if sum(apps_check["has_cask"].values()) > 0:
            self.log.info("Installed directly, but casks are available:")
            for d in app_dirs:
                if apps_check["has_cask"][d] == 0:
                    continue
                self.log.info(
                    f"{d.replace(os.environ['HOME'], '~'):{maxlen}s} : {apps_check['has_cask'][d]}"
                )
            self.log.info("")
        if sum(apps_check["appstore"].values()) > 0:
            self.log.info("Installed from Appstore")
            for d in app_dirs:
                if apps_check["appstore"][d] == 0:
                    continue
                self.log.info(
                    f"{d.replace(os.environ['HOME'], '~'):{maxlen}s} : {apps_check['appstore'][d]}"
                )
            self.log.info("")
        if sum(apps_check["no_cask"].values()) > 0:
            self.log.info("No casks")
            for d in app_dirs:
                if apps_check["no_cask"][d] == 0:
                    continue
                self.log.info(
                    f"{d.replace(os.environ['HOME'], '~'):{maxlen}s} : {apps_check['no_cask'][d]}"
                )
            self.log.info("")

    def make_pack_deps(self):
        """Make package dependencies."""
        packs = self.get("brew_list")
        self.pack_deps = {}
        for p in packs:
            deps = self.helper.proc(
                "brew deps --1 " + p, print_cmd=False, print_out=False
            )[1]
            self.pack_deps[p] = []
            for d in deps:
                if d in packs:
                    self.pack_deps[p].append(d)
        dep_packs = []
        for v in self.pack_deps.values():
            dep_packs.extend(v)
        self.top_packs = [x for x in packs if x not in dep_packs]

        def print_dep(p, depth=0):
            if depth > 2:
                self.log.info(f"#{' ' * (depth - 2)}", end="")
            self.log.info(p)
            for deps in self.pack_deps[p]:
                print_dep(deps, depth + 2)

        for p in packs:
            if p not in dep_packs:
                print_dep(p)

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
            self.debug_banner()
            self.repomgr(self.opt["command"])
            self.debug_banner()
            return

        # brew command
        if self.opt["command"] == "brew":
            self.debug_banner()
            self.brew_cmd()
            self.debug_banner()
            return

        # Initialize
        if self.opt["command"] in ["init", "dump"]:
            _ = self.initialize()
            return

        # Check input file
        # If the file doesn't exist, initialize it.
        self.check_input_file()

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

        # Cleanup non request
        if self.opt["command"] == "clean_non_request":
            self.debug_banner()
            self.clean_non_request()
            self.debug_banner()
            return

        # Cleanup
        if self.opt["command"] == "clean":
            self.debug_banner()
            self.cleanup()
            self.debug_banner()
            return

        # Install
        if self.opt["command"] == "install":
            self.debug_banner()
            self.install()
            self.debug_banner()
            return

        # Update
        if self.opt["command"] == "update":
            self.debug_banner()
            if not self.opt["noupgradeatupdate"]:
                self.helper.proc("brew update", dryrun=self.opt["dryrun"])
                self.helper.proc(
                    "brew upgrade --fetch-HEAD", dryrun=self.opt["dryrun"]
                )
                self.helper.proc(
                    "brew upgrade --cask", dryrun=self.opt["dryrun"]
                )
            if self.opt["repo"] != "":
                self.repomgr("pull")
            self.install()
            self.cleanup()
            if not self.opt["dryrun"]:
                _ = self.initialize(check=False)
            if self.opt["repo"] != "":
                self.repomgr("push")
            self.debug_banner()
            return

        # No command found
        raise RuntimeError(
            f"Wrong command: {self.opt['command']}\n"
            f"Execute `{__prog__} help` for more information."
        )
