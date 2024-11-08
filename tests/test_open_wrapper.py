from __future__ import annotations

from pathlib import Path

from . import brew_file


def test_open_non_existing_file(tmp_path: Path) -> None:
    content = 'abc\nxyz'
    with brew_file.OpenWrapper(tmp_path / 'more/path/file') as f:
        f.write(content)
    with Path(tmp_path / 'more/path/file').open() as f:
        assert f.read() == content
