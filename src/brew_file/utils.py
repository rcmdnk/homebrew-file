from __future__ import annotations

import logging
import os
import platform
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Type


class LogFormatter(logging.Formatter):
    """Formatter to add color to log messages."""

    def __init__(self) -> None:
        self.default_format = "%(message)s"
        self.formats = {
            logging.DEBUG: f"[DEBUG] {self.default_format}",
            logging.INFO: f"{self.default_format}",
            logging.WARNING: f"[WARNING] {self.default_format}",
            logging.ERROR: f"[ERROR] {self.default_format}",
            logging.CRITICAL: f"[CRITICAL] {self.default_format}",
        }
        if sys.stdout.isatty():
            colors = {
                logging.WARNING: "33",
                logging.ERROR: "31",
                logging.CRITICAL: "31",
            }
            for level in colors:
                self.formats[
                    level
                ] = f"\033[{colors[level]};1m{self.formats[level]}\033[m"

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        fmt = self.formats.get(record.levelno, self.default_format)
        formatter = logging.Formatter(fmt)
        return formatter.format(record)


def is_mac() -> bool:
    return platform.system() == "Darwin"


def to_bool(val: bool | int | str) -> bool:
    if isinstance(val, bool):
        return val
    if isinstance(val, int) or (isinstance(val, str) and val.isdigit()):
        return bool(int(val))
    if isinstance(val, str):
        if val.lower() == "true":
            return True
    return False


def to_num(val: bool | int | str) -> int:
    if isinstance(val, bool):
        return int(val)
    if isinstance(val, int) or (isinstance(val, str) and val.isdigit()):
        return int(val)
    if isinstance(val, str):
        if val.lower() == "true":
            return 1
    return 0


shell_envs: dict[str, str] = {
    "HOSTNAME": os.uname().nodename,
    "HOSTTYPE": os.uname().machine,
    "OSTYPE": subprocess.run(
        ["bash", "-c", "echo $OSTYPE"], capture_output=True, text=True
    ).stdout.strip(),
    "PLATFORM": sys.platform,
}


def expandpath(path: str | Path) -> Path:
    path = str(path)
    for k in shell_envs:
        for kk in [f"${k}", f"${{{k}}}"]:
            if kk in path:
                path = path.replace(kk, shell_envs[k])
    path = re.sub(
        r"(?<!\\)\$(\w+|\{([^}]*)\})",
        lambda x: os.getenv(x.group(2) or x.group(1), ""),
        path,
    )
    path = path.replace("\\$", "$")
    return Path(path).expanduser()


def home_tilde(path: str | Path) -> str:
    return str(path).replace(os.environ["HOME"], "~")


@dataclass
class OpenWrapper:
    """Wrapper function to open a file even if it doesn't exist."""

    name: str
    mode: str = "w"

    def __enter__(self) -> Any:
        if (
            Path(self.name).parent != ""
            and not Path(self.name).parent.exists()
        ):
            Path(self.name).parent.mkdir(parents=True)
        self.file = open(self.name, self.mode)
        return self.file

    def __exit__(
        self,
        exception_type: Type[BaseException],
        exception_value: BaseException,
        traceback: Any,
    ) -> bool:
        if exception_type is not None:
            return False
        self.file.close()
        return True


@dataclass
class StrRe(str):
    """Str wrapper to use regex especially for match-case."""

    var: str

    def __eq__(self, pattern: Any) -> bool:
        return True if re.search(pattern, self.var) is not None else False
