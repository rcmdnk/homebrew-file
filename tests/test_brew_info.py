from __future__ import annotations

from pathlib import Path

import pytest

from .brew_file import BrewHelper, BrewInfo, is_mac


def test_get_dir(brew_info: BrewInfo) -> None:
    assert brew_info.get_dir() == Path(f'{Path(__file__).parent}/files')


def test_check_file(brew_info: BrewInfo) -> None:
    assert brew_info.check_file()
    info = BrewInfo(helper=brew_info.helper, file=Path('not_exist'))
    assert not info.check_file()


def test_check_dir(brew_info: BrewInfo) -> None:
    assert brew_info.check_dir()
    info = BrewInfo(helper=brew_info.helper, file=Path('/not/exist'))
    assert not info.check_dir()


def test_clear_input(brew_info: BrewInfo) -> None:
    brew_info.brew_opt_input.update({'abc': 'abc'})
    brew_info.brew_input.extend(['abc', 'efg'])
    brew_info.tap_input.extend(['abc', 'efg'])
    brew_info.cask_input.extend(['abc', 'efg'])
    brew_info.appstore_input.extend(['abc', 'efg'])
    brew_info.main_input.extend(['abc', 'efg'])
    brew_info.file_input.extend(['abc', 'efg'])

    brew_info.before_input.extend(['abc', 'efg'])
    brew_info.after_input.extend(['abc', 'efg'])
    brew_info.cmd_input.extend(['abc', 'efg'])
    brew_info.cask_args_input.update({'abc': 'efg'})
    brew_info.clear_input()
    assert brew_info.brew_opt_input == {}
    assert brew_info.brew_input == []
    assert brew_info.tap_input == []
    assert brew_info.cask_input == []
    assert brew_info.appstore_input == []
    assert brew_info.main_input == []
    assert brew_info.file_input == []
    assert brew_info.before_input == []
    assert brew_info.after_input == []
    assert brew_info.cmd_input == []
    assert brew_info.cask_args_input == {}


def test_clear_list(brew_info: BrewInfo) -> None:
    brew_info.brew_opt_list.update({'abc': 'abc'})
    brew_info.brew_list.extend(['abc', 'efg'])
    brew_info.brew_full_list.extend(['abc', 'efg'])
    brew_info.tap_list.extend(['abc', 'efg'])
    brew_info.cask_list.extend(['abc', 'efg'])
    brew_info.appstore_list.extend(['abc', 'efg'])
    brew_info.main_list.extend(['abc', 'efg'])
    brew_info.file_list.extend(['abc', 'efg'])

    # brew_info.before_list = ['abc', 'efg']
    # brew_info.after_list = ['abc', 'efg']
    # brew_info.cmd_list = ['abc', 'efg']
    # brew_info.cask_args_list = ['abc', 'efg']

    # brew_info.cask_noargs_list = ['abc', 'efg']

    brew_info.clear_list()
    assert brew_info.brew_opt_list == {}
    assert brew_info.brew_list == []
    assert brew_info.brew_full_list == []
    assert brew_info.tap_list == []
    assert brew_info.cask_list == []
    assert brew_info.appstore_list == []
    assert brew_info.main_list == []
    assert brew_info.file_list == []


def test_clear(brew_info: BrewInfo) -> None:
    brew_info.brew_opt_input.update({'abc': 'abc'})
    brew_info.brew_input.extend(['abc', 'efg'])
    brew_info.tap_input.extend(['abc', 'efg'])
    brew_info.cask_input.extend(['abc', 'efg'])
    brew_info.appstore_input.extend(['abc', 'efg'])
    brew_info.main_input.extend(['abc', 'efg'])
    brew_info.file_input.extend(['abc', 'efg'])
    brew_info.before_input.extend(['abc', 'efg'])
    brew_info.after_input.extend(['abc', 'efg'])
    brew_info.cmd_input.extend(['abc', 'efg'])
    brew_info.cask_args_input.update({'abc': 'efg'})

    brew_info.brew_opt_list.update({'abc': 'abc'})
    brew_info.brew_list.extend(['abc', 'efg'])
    brew_info.brew_full_list.extend(['abc', 'efg'])
    brew_info.tap_list.extend(['abc', 'efg'])
    brew_info.cask_list.extend(['abc', 'efg'])
    brew_info.appstore_list.extend(['abc', 'efg'])
    brew_info.main_list.extend(['abc', 'efg'])
    brew_info.file_list.extend(['abc', 'efg'])
    brew_info.clear()
    assert brew_info.brew_opt_input == {}
    assert brew_info.brew_input == []
    assert brew_info.brew_input == []
    assert brew_info.tap_input == []
    assert brew_info.cask_input == []
    assert brew_info.appstore_input == []
    assert brew_info.main_input == []
    assert brew_info.file_input == []
    assert brew_info.before_input == []
    assert brew_info.after_input == []
    assert brew_info.cmd_input == []
    assert brew_info.cask_args_input == {}
    assert brew_info.brew_opt_list == {}
    assert brew_info.brew_list == []
    assert brew_info.brew_full_list == []
    assert brew_info.tap_list == []
    assert brew_info.cask_list == []
    assert brew_info.appstore_list == []
    assert brew_info.main_list == []
    assert brew_info.file_list == []


def test_input_to_list(brew_info: BrewInfo) -> None:
    brew_info.brew_opt_input.update({'brew_input': 'opt'})
    brew_info.brew_input.extend(['brew'])
    brew_info.tap_input.extend(['tap'])
    brew_info.cask_input.extend(['cask'])
    brew_info.appstore_input.extend(['appstore'])
    brew_info.main_input.extend(['main'])
    brew_info.file_input.extend(['file'])

    brew_info.brew_opt_list.update({'abc': 'abc'})
    brew_info.brew_list.extend(['abc', 'efg'])
    brew_info.tap_list.extend(['abc', 'efg'])
    brew_info.cask_list.extend(['abc', 'efg'])
    brew_info.appstore_list.extend(['abc', 'efg'])
    brew_info.main_list.extend(['abc', 'efg'])
    brew_info.file_list.extend(['abc', 'efg'])

    brew_info.input_to_list()

    assert brew_info.brew_opt_input == {'brew_input': 'opt'}
    assert brew_info.brew_input == ['brew']
    assert brew_info.tap_input == ['tap']
    assert brew_info.cask_input == ['cask']
    assert brew_info.appstore_input == ['appstore']
    assert brew_info.main_input == ['main']
    assert brew_info.file_input == ['file']

    assert brew_info.brew_opt_list == {'brew_input': 'opt', 'abc': 'abc'}
    assert brew_info.brew_list == ['brew']
    assert brew_info.tap_list == ['tap']
    assert brew_info.cask_list == ['cask']
    assert brew_info.appstore_list == ['appstore']
    assert brew_info.main_list == ['main']
    assert brew_info.file_list == ['file']


def test_sort(brew_info: BrewInfo) -> None:
    brew_info.tap_list.extend(
        ['rcmdnk/file', 'homebrew/cask', 'homebrew/bundle', 'homebrew/core'],
    )
    brew_info.appstore_list.extend(['111 ccc (2)', '222 aaa (1)', 'bbb'])
    brew_info.sort()
    assert brew_info.tap_list == [
        'homebrew/core',
        'homebrew/cask',
        'homebrew/bundle',
        'rcmdnk/file',
    ]
    assert brew_info.appstore_list == ['222 aaa (1)', 'bbb', '111 ccc (2)']


def test_get_list(brew_info: BrewInfo) -> None:
    brew_info.brew_input.extend(['brew'])
    brew_input = brew_info.get_list('brew_input')
    assert brew_input == ['brew']
    brew_input.append('brew2')
    assert brew_info.brew_input == ['brew']
    brew_input = brew_info.get_list('brew_input')
    assert brew_input == ['brew']


def test_get_dict(brew_info: BrewInfo) -> None:
    brew_info.brew_opt_input['brew'] = 'opt'
    brew_opt_input = brew_info.get_dict('brew_opt_input')
    assert brew_opt_input['brew'] == 'opt'
    brew_opt_input['brew2'] = 'opt2'
    assert list(brew_opt_input.keys()) == ['brew', 'brew2']
    brew_opt_input = brew_info.get_dict('brew_opt_input')
    assert list(brew_opt_input.keys()) == ['brew']


def test_get_files(brew_info: BrewInfo) -> None:
    files = brew_info.get_files()
    assert files == {
        'main': ['BrewfileMain'],
        'ext': [
            'BrewfileMain',
            'BrewfileExt',
            'BrewfileExt2',
            'BrewfileNotExist',
            '~/BrewfileHomeForTestingNotExists',
        ],
    }


def test_remove(brew_info: BrewInfo) -> None:
    brew_info.brew_input.extend(['aaa', 'bbb', 'ccc'])
    brew_info.remove('brew_input', 'bbb')
    assert brew_info.brew_input == ['aaa', 'ccc']
    brew_info.brew_opt_input.update({'aaa': 'aaa', 'bbb': 'bbb', 'ccc': 'ccc'})
    brew_info.remove('brew_opt_input', 'bbb')
    assert brew_info.brew_opt_input == {'aaa': 'aaa', 'ccc': 'ccc'}


def test_set_list_val(brew_info: BrewInfo) -> None:
    brew_info.brew_input.extend(['aaa', 'bbb'])
    brew_info.set_list_val('brew_input', ['ccc'])
    assert brew_info.brew_input == ['ccc']


def test_set_dict_val(brew_info: BrewInfo) -> None:
    brew_info.brew_opt_input.update({'aaa': 'aaa', 'bbb': 'bbb'})
    brew_info.set_dict_val('brew_opt_input', {'ccc': 'ccc'})
    assert brew_info.brew_opt_input == {'ccc': 'ccc'}


def test_add_to_list(brew_info: BrewInfo) -> None:
    brew_info.brew_input.extend(['aaa', 'bbb'])
    brew_info.add_to_list('brew_input', ['aaa', 'ccc'])
    assert brew_info.brew_input == ['aaa', 'bbb', 'ccc']


def test_add_to_dict(brew_info: BrewInfo) -> None:
    brew_info.brew_opt_input.update({'aaa': 'aaa', 'bbb': 'bbb'})
    brew_info.add_to_dict('brew_opt_input', {'aaa': 'ddd', 'ccc': 'ccc'})
    assert brew_info.brew_opt_input == {
        'aaa': 'ddd',
        'bbb': 'bbb',
        'ccc': 'ccc',
    }


def test_read(brew_info: BrewInfo) -> None:
    brew_info.read()
    assert brew_info.brew_opt_input == {'python@3.10': '', 'vim': ' --HEAD'}
    assert brew_info.brew_input == ['python@3.10', 'vim']
    if is_mac():
        assert brew_info.tap_input == [
            'homebrew/core',
            'homebrew/cask',
            'rcmdnk/rcmdnkcask',
        ]
        assert brew_info.cask_input == ['iterm2', 'font-migu1m']
        assert brew_info.appstore_input == ['Keynote']
    else:
        assert brew_info.tap_input == [
            'homebrew/core',
        ]
    assert brew_info.main_input == ['BrewfileMain']
    assert brew_info.file_input == [
        'BrewfileMain',
        'BrewfileExt',
        'BrewfileExt2',
        'BrewfileNotExist',
        '~/BrewfileHomeForTestingNotExists',
    ]
    assert brew_info.before_input == ['echo before']
    assert brew_info.after_input == ['echo after']
    assert brew_info.cmd_input == ['echo other commands']


def test_convert_option(brew_info: BrewInfo) -> None:
    brew_info.helper.opt['form'] = 'file'
    opt = brew_info.convert_option('--HEAD --test')
    assert opt == '--HEAD --test'
    brew_info.helper.opt['form'] = 'bundle'
    opt = brew_info.convert_option(' --HEAD --test')
    assert opt == ", args: ['HEAD', 'test']"


def test_packout(brew_info: BrewInfo) -> None:
    brew_info.helper.opt['form'] = 'file'
    assert brew_info.packout('package') == 'package'
    brew_info.helper.opt['form'] = 'bundle'
    assert brew_info.packout('package') == "'package'"


def test_mas_pack(brew_info: BrewInfo) -> None:
    brew_info.helper.opt['form'] = 'file'
    assert (
        brew_info.mas_pack('409183694   Keynote  (12.2.1)')
        == '409183694   Keynote  (12.2.1)'
    )
    brew_info.helper.opt['form'] = 'bundle'
    assert (
        brew_info.mas_pack('409183694   Keynote  (12.2.1)')
        == "'Keynote (12.2.1)', id: 409183694"
    )


def test_invalid_format(tmp_path: Path) -> None:
    helper = BrewHelper(opt={'form': 'invalid-format'})
    info = BrewInfo(helper=helper, file=tmp_path / 'Brewfile')
    with pytest.raises(ValueError, match='Invalid format') as excinfo:
        info.write()
    assert (
        str(excinfo.value)
        == 'Invalid format: "invalid-format".\nUse "file", "brewdler", "bundle", "command" or "cmd".'
    )
