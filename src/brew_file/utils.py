from __future__ import annotations

import logging
import os
import platform
import re
import subprocess
import sys
from _io import TextIOWrapper
from dataclasses import dataclass
from pathlib import Path
from types import TracebackType
from typing import Literal


class LogFormatter(logging.Formatter):
    """Formatter to add color to log messages."""

    def __init__(self) -> None:
        self.default_format = '%(message)s'
        self.formats = {
            logging.DEBUG: f'[DEBUG] {self.default_format}',
            logging.INFO: f'{self.default_format}',
            logging.WARNING: f'[WARNING] {self.default_format}',
            logging.ERROR: f'[ERROR] {self.default_format}',
            logging.CRITICAL: f'[CRITICAL] {self.default_format}',
        }
        if sys.stdout.isatty():
            colors = {
                logging.WARNING: '33',
                logging.ERROR: '31',
                logging.CRITICAL: '31',
            }
            for level, color in colors.items():
                self.formats[level] = (
                    f'\033[{color};1m{self.formats[level]}\033[m'
                )

    def format(self, record: logging.LogRecord) -> str:
        fmt = self.formats.get(record.levelno, self.default_format)
        formatter = logging.Formatter(fmt)
        return formatter.format(record)


def is_mac() -> bool:
    return platform.system() == 'Darwin'


def to_bool(val: bool | int | str) -> bool:
    if isinstance(val, bool):
        return val
    if isinstance(val, int) or (
        isinstance(val, str) and val.lstrip('+-').isdigit()
    ):
        return bool(int(val))
    return isinstance(val, str) and val.lower() == 'true'


def to_num(val: bool | int | str) -> int:
    if isinstance(val, bool):
        return int(val)
    if isinstance(val, int) or (
        isinstance(val, str) and val.lstrip('+-').isdigit()
    ):
        return int(val)
    if isinstance(val, str) and val.lower() == 'true':
        return 1
    return 0


shell_envs: dict[str, str] = {
    'HOSTNAME': os.uname().nodename,
    'HOSTTYPE': os.uname().machine,
    'OSTYPE': subprocess.run(
        ['bash', '-c', 'echo $OSTYPE'],
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip(),
    'PLATFORM': sys.platform,
}


def expandpath(path: str | Path) -> Path:
    path = str(path)
    for k, v in shell_envs.items():
        for kk in [f'${k}', f'${{{k}}}']:
            if kk in path:
                path = path.replace(kk, v)
    path = re.sub(
        r'(?<!\\)\$(\w+|\{([^}]*)\})',
        lambda x: os.getenv(x.group(2) or x.group(1), ''),
        path,
    )
    path = path.replace('\\$', '$')
    return Path(path).expanduser()


def home_tilde(path: str | Path) -> str:
    return str(path).replace(os.environ['HOME'], '~')


@dataclass
class OpenWrapper:
    """Wrapper function to open a file even if it doesn't exist."""

    name: str
    mode: Literal['w', 'r', 'a'] = 'w'

    def __enter__(self) -> TextIOWrapper:
        Path(self.name).parent.mkdir(parents=True, exist_ok=True)
        self.file = Path(self.name).open(self.mode)
        return self.file

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        if exception_type is not None:
            return False
        self.file.close()
        return True


@dataclass
class StrRe(str):
    """Str wrapper to use regex especially for match-case."""

    var: str

    def __eq__(self, pattern: object) -> bool:
        return re.search(str(pattern), self.var) is not None
