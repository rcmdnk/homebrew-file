import tempfile
from . import brew_file


def test_open_output_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        content = 'abc\nxyz'
        with brew_file.OpenWrapper(f"{tmpdir}/more/path/file") as f:
            f.write(content)
        with open(f"{tmpdir}/more/path/file") as f:
            assert f.read() == content
