import os
import platform
import re
import subprocess
import sys
from dataclasses import dataclass, field
from io import StringIO
from pathlib import Path
from typing import Any, Union


def is_mac() -> bool:
    return platform.system() == "Darwin"


def to_bool(val: Union[bool, int, str]) -> bool:
    if isinstance(val, bool):
        return val
    if isinstance(val, int) or (isinstance(val, str) and val.isdigit()):
        return bool(int(val))
    if isinstance(val, str):
        if val.lower() == "true":
            return True
    return False


def to_num(val: Union[bool, int, str]) -> int:
    if isinstance(val, bool):
        return int(val)
    if isinstance(val, int) or (isinstance(val, str) and val.isdigit()):
        return int(val)
    if isinstance(val, str):
        if val.lower() == "true":
            return 1
    return 0


shell_envs = {
    "HOSTNAME": os.uname().nodename,
    "HOSTTYPE": os.uname().machine,
    "OSTYPE": subprocess.run(
        ["bash", "-c", "echo $OSTYPE"], capture_output=True, text=True
    ).stdout.strip(),
    "PLATFORM": sys.platform,
}


def expandpath(path: Union[str, Path]) -> Path:
    path = str(path)
    for k in shell_envs:
        for kk in [f"${k}", f"${{{k}}}"]:
            if kk in path:
                path = path.replace(kk, shell_envs[k])
    path = re.sub(
        r"(?<!\\)\$(\w+|\{([^}]*)\})",
        lambda x: os.environ.get(x.group(2) or x.group(1), ""),
        path,
    )
    path = path.replace("\\$", "$")
    return Path(path).expanduser()


@dataclass
class OpenWrapper:
    """Wrapper function to open a file even if it doesn't exist."""

    name: str
    mode: str = "w"

    def __enter__(self):
        if (
            Path(self.name).parent != ""
            and not Path(self.name).parent.exists()
        ):
            Path(self.name).parent.mkdir(parents=True)
        self.file = open(self.name, self.mode)
        return self.file

    def __exit__(self, exception_type, exception_value, traceback):
        if exception_type is not None:
            return False
        self.file.close()
        return True


@dataclass
class Tee:
    """Module to write out in two ways at once."""

    out1: Any
    out2: Any = field(default_factory=lambda: sys.stdout)
    use2: bool = True

    def __post_init__(self):
        if isinstance(self.out1, str) or isinstance(self.out1, Path):
            self.out1name = str(self.out1)
            self.out1 = StringIO()
        else:
            self.out1name = ""
        if self.use2:
            if isinstance(self.out2, str) or isinstance(self.out2, Path):
                self.out2name = str(self.out2)
                self.out2 = StringIO()
            else:
                self.out2name = ""

    def __del__(self):
        if self.out1name != "":
            self.out1.close()
        if self.use2:
            if self.out2name != "":
                self.out2.close()

    def write(self, text):
        """Write w/o line break."""
        self.out1.write(text)
        if self.use2:
            self.out2.write(text)

    def writeln(self, text):
        """Write w/ line break."""
        self.out1.write(text + "\n")
        if self.use2:
            self.out2.write(text + "\n")

    def flush(self):
        """Flush the output."""
        self.out1.flush()
        if self.use2:
            self.out2.flush()

    def close(self):
        """Close output files."""
        if self.out1name != "":
            with OpenWrapper(self.out1name, "w") as f:
                f.write(self.out1.getvalue())
        if self.use2:
            if self.out2name != "":
                with OpenWrapper(self.out2name, "w") as f:
                    f.write(self.out2.getvalue())
        self.__del__()


@dataclass
class StrRe(str):
    """Str wrapper to use regex especially for match-case."""

    var: str

    def __eq__(self, pattern) -> bool:
        return True if re.search(pattern, self.var) is not None else False
