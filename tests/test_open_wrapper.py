import tempfile

from . import brew_file


def test_open_non_existing_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        content = "abc\nxyz"
        with brew_file.OpenWrapper(f"{tmpdir}/more/path/file") as f:
            f.write(content)
        with open(f"{tmpdir}/more/path/file") as f:
            assert f.read() == content


def test_raise_error():
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            content = "abc\nxyz"
            with brew_file.OpenWrapper(f"{tmpdir}/more/path/file") as f:
                raise RuntimeError("Error")
            with open(f"{tmpdir}/more/path/file") as f:
                assert f.read() == content
    except RuntimeError as e:
        assert str(e) == "Error"
