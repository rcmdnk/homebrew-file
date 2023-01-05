def test_capsys(capsys):
    print('hogeratta')
    captured = capsys.readouterr()
    assert captured.out == 'hogeratta\n'
    assert captured.err == ''


def test_capfd(capfd):
    print('hogeratta')
    captured = capfd.readouterr()
    assert captured.out == 'hogeratta\n'
    assert captured.err == ''

