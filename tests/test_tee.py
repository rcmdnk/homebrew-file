import logging

from . import brew_file


def test_tee(caplog, tmp_path):
    caplog.set_level(logging.DEBUG)
    out = brew_file.Tee(tmp_path / "out1")
    out.write("test\n")
    out.writeln("test_ln")
    out.close()
    with open(tmp_path / "out1") as f:
        assert f.read() == "test\ntest_ln\n"
    assert not caplog.record_tuples


def test_tee_logger(caplog, tmp_path):
    caplog.set_level(logging.DEBUG)
    logger = logging.getLogger("test")
    out = brew_file.Tee(tmp_path / "out1", logger)
    out.write("test\n")
    out.writeln("test_ln")
    out.close()
    with open(tmp_path / "out1") as f:
        assert f.read() == "test\ntest_ln\n"
    assert caplog.record_tuples == [
        ("test", logging.INFO, "test\n"),
        ("test", logging.INFO, "test_ln\n"),
    ]
