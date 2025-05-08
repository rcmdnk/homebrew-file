from __future__ import annotations

from pathlib import Path

import pytest

from . import brew_file


def test_open_non_existing_file(tmp_path: Path) -> None:
    # Test creating a new file
    content = 'abc\nxyz'
    with brew_file.OpenWrapper(tmp_path / 'more/path/file') as f:
        f.write(content)
    with Path(tmp_path / 'more/path/file').open() as f:
        assert f.read() == content


def test_open_existing_file(tmp_path: Path) -> None:
    # Create file first
    test_file = tmp_path / 'test.txt'
    content = 'initial content'
    test_file.write_text(content)

    # Test writing to existing file
    new_content = 'new content'
    with brew_file.OpenWrapper(test_file) as f:
        f.write(new_content)
    assert test_file.read_text() == new_content


def test_open_with_different_modes(tmp_path: Path) -> None:
    test_file = tmp_path / 'test.txt'

    # Test write mode
    with brew_file.OpenWrapper(test_file, 'w') as f:
        f.write('test')

    # Test read mode
    with brew_file.OpenWrapper(test_file, 'r') as f:
        assert f.read() == 'test'

    # Test append mode
    with brew_file.OpenWrapper(test_file, 'a') as f:
        f.write('_append')
    assert test_file.read_text() == 'test_append'


def test_error_handling(tmp_path: Path) -> None:
    test_file = tmp_path / 'test.txt'

    # Test handling of write error
    Path(tmp_path).chmod(0o444)  # Make directory read-only
    with pytest.raises(PermissionError), brew_file.OpenWrapper(test_file) as f:
        f.write('test')
    Path(tmp_path).chmod(0o755)  # Restore permissions
