import tempfile

from . import brew_file


def test_tee(capsys):
    with tempfile.TemporaryDirectory() as tmpdir:
        out = brew_file.Tee(f"{tmpdir}/out1")
        out.write("test\n")
        out.writeln("test_ln")
        out.flush()
        out.close()
        with open(f"{tmpdir}/out1") as f:
            assert f.read() == "test\ntest_ln\n"
    captured = capsys.readouterr()
    assert captured.out == "test\ntest_ln\n"
    assert captured.err == ""


def test_tee_out2_file(capfd):
    with tempfile.TemporaryDirectory() as tmpdir:
        out = brew_file.Tee(f"{tmpdir}/out1", f"{tmpdir}/out2")
        out.write("test\n")
        out.writeln("test_ln")
        out.flush()
        out.close()
        with open(f"{tmpdir}/out1") as f:
            assert f.read() == "test\ntest_ln\n"
        with open(f"{tmpdir}/out2") as f:
            assert f.read() == "test\ntest_ln\n"
    captured = capfd.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_tee_no_out2(capfd):
    with tempfile.TemporaryDirectory() as tmpdir:
        out = brew_file.Tee(f"{tmpdir}/out1", use2=False)
        out.write("test\n")
        out.writeln("test_ln")
        out.flush()
        out.close()
        with open(f"{tmpdir}/out1") as f:
            assert f.read() == "test\ntest_ln\n"
    captured = capfd.readouterr()
    assert captured.out == ""
    assert captured.err == ""
