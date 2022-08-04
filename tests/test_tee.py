import tempfile
from . import brew_file


def test_tee():
    with tempfile.TemporaryDirectory() as tmpdir:
        out = brew_file.Tee(f"{tmpdir}/out1", f"{tmpdir}/out2")
        out.write("test\n")
        out.flush()
        out.close()
        with open(f"{tmpdir}/out1") as f:
            f.read() == "test\n"
        with open(f"{tmpdir}/out2") as f:
            f.read() == "test\n"
