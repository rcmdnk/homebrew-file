import logging
import os
import shlex
import subprocess
from dataclasses import dataclass, field
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
        try:
            if separate_err:
                if print_err:
                    stderr = subprocess.PIPE
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
            )
            out, err = p.communicate()
            ret = p.returncode
        except OSError as e:
            if not separate_err:
                out = str(e) + "\n"
                err = None
            elif print_err:
                out = ""
                err = str(e) + "\n"
            ret = e.errno

        if exit_on_err and ret != 0:
            if err is not None:
                out += err
            raise CmdError(out, ret)
        if print_out:
            self.log.info(out)
        if err and print_err:
            self.log.error(err)
        return ret, out.splitlines()

    def banner(self, text: str) -> None:
        width = 0
        for line in text.split("\n"):
            if width < len(line):
                width = len(line)
        self.log.info(
            f"\n{'#' * width}\n{text}\n{'#' * width}\n",
        )

    def brew_val(self, name: str) -> Any:
        if name not in self.opt:
            self.opt[name] = self.proc("brew --" + name, False, False)[1][0]
        return self.opt[name]
