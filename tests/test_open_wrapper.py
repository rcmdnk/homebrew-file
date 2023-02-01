from . import brew_file


def test_open_non_existing_file(tmp_path):
    content = "abc\nxyz"
    with brew_file.OpenWrapper(tmp_path / "more/path/file") as f:
        f.write(content)
    with open(tmp_path / "more/path/file") as f:
        assert f.read() == content


def test_raise_error(tmp_path):
    try:
        content = "abc\nxyz"
        with brew_file.OpenWrapper(tmp_path / "more/path/file") as f:
            raise RuntimeError("Error")
        with open(tmp_path / "more/path/file") as f:
            assert f.read() == content
    except RuntimeError as e:
        assert str(e) == "Error"
