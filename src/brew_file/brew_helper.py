import os
import shlex
import subprocess
import sys
from dataclasses import dataclass, field


@dataclass
class BrewHelper:
    """Helper functions for BrewFile."""

    opt: dict = field(default_factory=dict)
    colors: dict = field(
        default_factory=lambda: {
            "black": "30",
            "red": "31",
            "green": "32",
            "yellow": "33",
            "blue": "34",
            "magenta": "35",
            "lightblue": 36,
            "white": 37,
        }
    )

    def readstdout(self, proc):
        for line in iter(proc.stdout.readline, ""):
            line = line.rstrip()
            if line == "":
                continue
            yield line

    def proc(
        self,
        cmd,
        print_cmd=True,
        print_out=True,
        exit_on_err=True,
        separate_err=False,
        print_err=True,
        verbose=1,
        env=None,
        dryrun=False,
    ):
        """Get process output."""
        if env is None:
            env = {}
        if not isinstance(cmd, list):
            cmd = shlex.split(cmd)
        cmd_orig = " ".join(["$"] + cmd)
        if cmd[0] == "brew":
            cmd[0] = self.opt.get("brew_cmd", "brew")
        if print_cmd or dryrun:
            self.info(cmd_orig, verbose)
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
                    stderr = open(os.devnull, "w")
            else:
                stderr = subprocess.STDOUT
            p = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=stderr,
                text=True,
                env=all_env,
            )
            if hasattr(stderr, "close"):
                stderr.close()
            for line in self.readstdout(p):
                lines.append(line)
                if print_out:
                    self.info(line, verbose)
            ret = p.wait()
        except OSError as e:
            if print_out:
                lines = [" ".join(cmd) + ": " + str(e)]
                self.info(lines[0].strip(), verbose)
            ret = -1

        if exit_on_err and ret != 0:
            if not (print_out and self.opt.get("verbose", 1) >= verbose):
                print("\n".join(lines))
            self.err("Failed at command: " + " ".join(cmd))
            sys.exit(ret)

        return ret, lines

    def out(self, text, verbose=100, color=""):
        if self.opt.get("verbose", 1) < verbose:
            return
        pre = post = ""
        if color != "" and sys.stdout.isatty():
            if color in self.colors:
                pre = "\033[" + self.colors[color] + ";1m"
                post = "\033[m"
        print(pre + text + post)

    def info(self, text, verbose=2):
        self.out(text, verbose)

    def warn(self, text, verbose=1):
        self.out("[WARNING]: " + text, verbose, "yellow")

    def err(self, text, verbose=0):
        self.out("[ERROR]: " + text, verbose, "red")

    def banner(self, text, verbose=1):
        width = 0
        for line in text.split("\n"):
            if width < len(line):
                width = len(line)
        self.out(
            "\n" + "#" * width + "\n" + text + "\n" + "#" * width + "\n",
            verbose,
        )

    def brew_val(self, name):
        if name not in self.opt:
            self.opt[name] = self.proc("brew --" + name, False, False)[1][0]
        return self.opt[name]
