import sys

from . import brew_file


def test_tee(capsys, tmp_path):
    out = brew_file.Tee(tmp_path / "out1")
    out.write("test\n")
    out.writeln("test_ln")
    out.flush()
    out.close()
    with open(tmp_path / "out1") as f:
        assert f.read() == "test\ntest_ln\n"
    sys.stdout.flush()
    captured = capsys.readouterr()
    assert captured.out == "test\ntest_ln\n"
    assert captured.err == ""


def test_tee_out2_file(capsys, tmp_path):
    out = brew_file.Tee(tmp_path / "out1", tmp_path / "out2")
    out.write("test\n")
    out.writeln("test_ln")
    out.flush()
    out.close()
    with open(tmp_path / "out1") as f:
        assert f.read() == "test\ntest_ln\n"
    with open(tmp_path / "out2") as f:
        assert f.read() == "test\ntest_ln\n"
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_tee_no_out2(capsys, tmp_path):
    out = brew_file.Tee(tmp_path / "out1", use2=False)
    out.write("test\n")
    out.writeln("test_ln")
    out.flush()
    out.close()
    with open(tmp_path / "out1") as f:
        assert f.read() == "test\ntest_ln\n"
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
