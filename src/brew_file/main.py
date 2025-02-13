from __future__ import annotations

import argparse
import logging
import sys
from typing import Any

from .brew_file import BrewFile
from .brew_helper import CmdError
from .info import __date__, __description__, __prog__, __version__
from .utils import LogFormatter


def main() -> int:
    log = logging.getLogger(__name__.split('.')[0])
    log.setLevel(logging.INFO)
    ch = logging.StreamHandler(stream=sys.stdout)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(LogFormatter())
    log.addHandler(ch)

    # Prepare BrewFile
    b = BrewFile()

    # Pre Parser
    arg_parser_opts: dict[str, Any] = {
        'add_help': False,
        'allow_abbrev': False,
    }
    pre_parser = argparse.ArgumentParser(
        usage=f'{__prog__}...',
        **arg_parser_opts,
    )
    group = pre_parser.add_mutually_exclusive_group()
    group.add_argument(
        '-i',
        '--init',
        action='store_const',
        dest='command',
        const='init',
    )
    group.add_argument(
        '-s',
        '--set_repo',
        action='store_const',
        dest='command',
        const='set_repo',
    )
    group.add_argument(
        '--set_local',
        action='store_const',
        dest='command',
        const='set_local',
    )
    group.add_argument(
        '-c',
        '--clean',
        action='store_const',
        dest='command',
        const='clean',
    )
    group.add_argument(
        '-u',
        '--update',
        action='store_const',
        dest='command',
        const='update',
    )
    group.add_argument(
        '-e',
        '--edit',
        action='store_const',
        dest='command',
        const='edit',
    )
    group.add_argument(
        '--cat',
        action='store_const',
        dest='command',
        const='cat',
    )
    group.add_argument(
        '--commands',
        action='store_const',
        dest='command',
        const='commands',
    )
    group.add_argument(
        '-v',
        '--version',
        action='store_const',
        dest='command',
        const='version',
    )

    # Parent parser
    file_parser = argparse.ArgumentParser(**arg_parser_opts)
    file_parser.add_argument(
        '-f',
        '--file',
        action='store',
        dest='input',
        default=b.opt['input'],
        help='Set input file (default: %(default)s). '
        'You can set input file by environmental variable, '
        'HOMEBREW_BREWFILE, like:\n'
        '    export HOMEBREW_BREWFILE=~/.brewfile',
    )

    backup_parser = argparse.ArgumentParser(**arg_parser_opts)
    backup_parser.add_argument(
        '-b',
        '--backup',
        action='store',
        dest='backup',
        default=b.opt['backup'],
        help='Set backup file (default: %(default)s). '
        'If it is empty, no backup is made. '
        'You can set backup file by environmental variable, '
        'HOMEBREW_BREWFILE_BACKUP, like:\n'
        '    export HOMEBREW_BREWFILE_BACKUP=~/brewfile.backup',
    )

    format_parser = argparse.ArgumentParser(**arg_parser_opts)
    format_parser.add_argument(
        '-F',
        '--format',
        '--form',
        action='store',
        dest='form',
        default=b.opt['form'],
        help='Set input file format (default: %(default)s). \n'
        'file (or none)    : brew vim --HEAD --with-lua\n'
        "brewdler or bundle: brew 'vim', args: ['with-lua', 'HEAD']\n"
        '  Compatible with '
        '[homebrew-bundle]'
        '(https://github.com/Homebrew/homebrew-bundle).\n'
        'command or cmd    : brew install vim --HEAD --with-lua\n'
        '  Can be used as a shell script.\n',
    )

    leaves_parser = argparse.ArgumentParser(**arg_parser_opts)
    leaves_parser.add_argument(
        '--leaves',
        action='store_true',
        dest='leaves',
        default=b.opt['leaves'],
        help='Make list only for leaves (taken by `brew leaves`). '
        'You can set this by environmental variable, '
        'HOMEBREW_BREWFILE_LEAVES, like:\n'
        '    export HOMEBREW_BREWFILE_LEAVES=1',
    )

    on_request_parser = argparse.ArgumentParser(**arg_parser_opts)
    on_request_parser.add_argument(
        '--on_request',
        action='store_true',
        dest='on_request',
        default=b.opt['on_request'],
        help='Make list only for packages installed on request. '
        "This option is given priority over 'leaves'. "
        'You can set this by environmental variable, '
        'HOMEBREW_BREWFILE_ON_REQUEST, like:\n'
        '    export HOMEBREW_BREWFILE_ON_REQUEST=1',
    )

    top_packages_parser = argparse.ArgumentParser(**arg_parser_opts)
    top_packages_parser.add_argument(
        '--top_packages',
        action='store',
        dest='top_packages',
        default=b.opt['top_packages'],
        help='Packages to be listed even if they are under dependencies '
        "and `leaves`/'on_request' option is used. "
        'You can set this by environmental variable, '
        "HOMEBREW_BREWFILE_TOP_PACKAGES (',' separated), like:\n"
        '    export HOMEBREW_BREWFILE_TOP_PACKAGES=go,coreutils',
    )

    full_name_parser = argparse.ArgumentParser(**arg_parser_opts)
    full_name_parser.add_argument(
        '--full-name',
        action='store_true',
        dest='full_name',
        default=b.opt['full_name'],
        help='Use full names (tap/package) for packages. '
        'You can set this by environmental variable, '
        'HOMEBREW_BREWFILE_FULL_NAME, like:\n'
        '    export HOMEBREW_BREWFILE_FULL_NAME=1',
    )

    noupgradeatupdate_parser = argparse.ArgumentParser(**arg_parser_opts)
    noupgradeatupdate_parser.add_argument(
        '-U',
        '--noupgrade',
        action='store_true',
        dest='noupgradeatupdate',
        default=b.opt['noupgradeatupdate'],
        help='Do not execute `brew update/brew upgrade`'
        ' at `brew file update`.',
    )

    repo_parser = argparse.ArgumentParser(**arg_parser_opts)
    repo_parser.add_argument(
        '-r',
        '--repo',
        action='store',
        dest='repo',
        default=b.opt['repo'],
        help='Set repository name. Use with set_repo.',
    )

    fetch_parser = argparse.ArgumentParser(**arg_parser_opts)
    fetch_parser.add_argument(
        '--fetch-HEAD',
        action='store_true',
        dest='fetch_head',
        default=b.opt['fetch_head'],
        help='Fetch HEAD at update.',
    )

    link_parser = argparse.ArgumentParser(**arg_parser_opts)
    link_parser.add_argument(
        '-n',
        '--nolink',
        action='store_false',
        dest='link',
        default=b.opt['link'],
        help="Don't make links for Apps.",
    )

    caskonly_parser = argparse.ArgumentParser(**arg_parser_opts)
    caskonly_parser.add_argument(
        '--caskonly',
        action='store_true',
        dest='caskonly',
        default=b.opt['caskonly'],
        help='Write out only cask related packages',
    )

    appstore_parser = argparse.ArgumentParser(**arg_parser_opts)
    appstore_parser.add_argument(
        '--appstore',
        action='store',
        dest='appstore',
        default=b.opt['appstore'],
        help='Set AppStore application check level.\n'
        '0: do not check,\n'
        '1: check and manage,\n'
        '2: check for installation, but do not add to Brewfile when Apps are added. '
        'You can set the level by environmental variable:\n'
        '    export HOMEBREW_BREWFILE_APPSTORE=0',
    )

    no_appstore_parser = argparse.ArgumentParser(**arg_parser_opts)
    no_appstore_parser.add_argument(
        '--no_appstore',
        action='store_true',
        dest='no_appstore',
        default=b.opt['no_appstore'],
        help='Set AppStore application check level to 0. '
        "(legacy option, works same as '--appstore 0'.)",
    )

    all_files_parser = argparse.ArgumentParser(**arg_parser_opts)
    all_files_parser.add_argument(
        '--all_files',
        action='store_true',
        dest='all_files',
        default=b.opt['all_files'],
        help='Show all Brewfile files including non-existing files.',
    )

    dryrun_parser = argparse.ArgumentParser(**arg_parser_opts)
    dryrun_parser.add_argument(
        '-d',
        '--dry_run',
        action='store_true',
        dest='dryrun',
        default=b.opt['dryrun'],
        help='Set dry run mode.',
    )

    yn_parser = argparse.ArgumentParser(**arg_parser_opts)
    yn_parser.add_argument(
        '-y',
        '--yes',
        action='store_true',
        dest='yn',
        default=b.opt['yn'],
        help='Answer yes to all yes/no questions.',
    )

    verbose_parser = argparse.ArgumentParser(**arg_parser_opts)
    verbose_parser.add_argument(
        '-V',
        '--verbose',
        action='store',
        choices=[
            'debug',
            'info',
            'warning',
            'error',
            'critical',
        ],
        dest='verbose',
        default=b.opt['verbose'],
        help='Verbose level',
    )

    help_parser = argparse.ArgumentParser(**arg_parser_opts)
    help_parser.add_argument(
        '-h',
        '--help',
        action='store_true',
        dest='help',
        default=False,
        help='Print Help (this message) and exit.',
    )

    min_parsers = [
        file_parser,
        backup_parser,
        format_parser,
        leaves_parser,
        on_request_parser,
        top_packages_parser,
        full_name_parser,
        appstore_parser,
        no_appstore_parser,
        caskonly_parser,
        yn_parser,
        verbose_parser,
    ]
    formatter = argparse.RawTextHelpFormatter
    subparser_opts: dict[str, Any] = {
        'formatter_class': formatter,
        'allow_abbrev': False,
    }

    # Main parser
    parser = argparse.ArgumentParser(
        prog=__prog__,
        parents=[
            file_parser,
            backup_parser,
            format_parser,
            leaves_parser,
            on_request_parser,
            top_packages_parser,
            full_name_parser,
            noupgradeatupdate_parser,
            repo_parser,
            fetch_parser,
            link_parser,
            caskonly_parser,
            appstore_parser,
            no_appstore_parser,
            dryrun_parser,
            yn_parser,
            verbose_parser,
            help_parser,
        ],
        formatter_class=formatter,
        description=__description__,
        epilog='Check https://homebrew-file.readthedocs.io for more details.',
        **arg_parser_opts,
    )

    subparsers = parser.add_subparsers(
        title='subcommands',
        metavar='[command]',
        help='',
        dest='command',
    )

    help_doc = (
        'Install packages in BREWFILE if no <package> is given. '
        'If <package> is given, the package is installed and it is added in BREWFILE.'
    )
    subparsers.add_parser(
        'install',
        description=help_doc,
        help=help_doc,
        parents=[*min_parsers, dryrun_parser],
        **subparser_opts,
    )
    help_doc = (
        'Execute brew command, and update BREWFILE. '
        "Use 'brew noinit <brew command>' to suppress Brewfile initialization."
    )
    subparsers.add_parser(
        'brew',
        description=help_doc,
        help=help_doc,
        parents=min_parsers,
        **subparser_opts,
    )
    help_doc = (
        'or dump/-i/--init\n'
        'Initialize/Update BREWFILE with installed packages.'
    )
    subparsers.add_parser(
        'init',
        description=help_doc,
        help=help_doc,
        parents=[*min_parsers, link_parser, repo_parser],
        **subparser_opts,
    )
    subparsers.add_parser(
        'dump',
        parents=[*min_parsers, link_parser, repo_parser],
        **subparser_opts,
    )
    help_doc = (
        'or -s/--set_repo\n'
        'Set BREWFILE repository (e.g. rcmdnk/Brewfile or full path to your repository).'
    )
    subparsers.add_parser(
        'set_repo',
        description=help_doc,
        help=help_doc,
        parents=[*min_parsers, repo_parser],
        **subparser_opts,
    )
    help_doc = 'or --set_local\nSet BREWFILE to local file.'
    subparsers.add_parser(
        'set_local',
        description=help_doc,
        help=help_doc,
        parents=min_parsers,
        **subparser_opts,
    )
    help_doc = 'Update BREWFILE from the repository.'
    subparsers.add_parser(
        'pull',
        description=help_doc,
        help=help_doc,
        parents=[*min_parsers, dryrun_parser],
        **subparser_opts,
    )
    help_doc = 'Push your BREWFILE to the repository.'
    subparsers.add_parser(
        'push',
        description=help_doc,
        help=help_doc,
        parents=[*min_parsers, dryrun_parser],
        **subparser_opts,
    )
    help_doc = (
        'or -c/--clean\n'
        'Cleanup. Uninstall packages not in the list. Untap packages not in the list. Cleanup cache (brew cleanup and delete rm -rf $(brew --cache)).'
    )
    subparsers.add_parser(
        'clean',
        description=help_doc,
        help=help_doc,
        parents=[*min_parsers, dryrun_parser],
        **subparser_opts,
    )
    help_doc = (
        'or --clean_non_request.\n'
        'Uninstall packages which were installed as dependencies but parent packages of which were already uninstalled.'
    )
    subparsers.add_parser(
        'clean_non_request',
        description=help_doc,
        help=help_doc,
        parents=[*min_parsers, dryrun_parser],
        **subparser_opts,
    )
    help_doc = (
        'or -u/--update\n'
        'Do brew update/upgrade, cask upgrade, pull, install, init and push. In addition, pull and push will be done if the repository is assigned.\nIt will enforce the state recorded in the Brewfile, potentially removing packages installed without `brew-wrap`. If you want to keep all packages in the system, you should better to run `brew file init` before running `brew file update`.'
    )
    subparsers.add_parser(
        'update',
        description=help_doc,
        help=help_doc,
        parents=[
            *min_parsers,
            fetch_parser,
            link_parser,
            noupgradeatupdate_parser,
            dryrun_parser,
        ],
        **subparser_opts,
    )
    help_doc = 'or -e/--edit\nEdit input files.'
    subparsers.add_parser(
        'edit',
        description=help_doc,
        help=help_doc,
        parents=[file_parser],
        **subparser_opts,
    )
    help_doc = 'or --cat\nShow contents of input files.'
    subparsers.add_parser(
        'cat',
        description=help_doc,
        help=help_doc,
        parents=[file_parser],
        **subparser_opts,
    )
    help_doc = 'Check applications for Cask.'
    subparsers.add_parser(
        'casklist',
        description=help_doc,
        help=help_doc,
        parents=[verbose_parser],
        **subparser_opts,
    )
    help_doc = "Get Brewfile's full path, including additional files."
    subparsers.add_parser(
        'get_files',
        description=help_doc,
        help=help_doc,
        parents=[file_parser, all_files_parser],
        **subparser_opts,
    )
    help_doc = 'or --commands\nShow commands.'
    subparsers.add_parser(
        'commands',
        description=help_doc,
        help=help_doc,
        **subparser_opts,
    )
    help_doc = 'or -v/--version\nShow version.'
    subparsers.add_parser(
        'version',
        description=help_doc,
        help=help_doc,
        **subparser_opts,
    )
    help_doc = 'or -h/--help\nPrint Help (this message) and exit.'
    subparsers.add_parser(
        'help',
        description=help_doc,
        help=help_doc,
        **subparser_opts,
    )

    info = f'{parser.format_usage()}\n\nExecute `{__prog__} help` to get help.\n\nRefer https://homebrew-file.readthedocs.io for more details.'
    if len(sys.argv) == 1:
        log.info(info)
        return 0

    if sys.argv[1] == 'brew':
        args = sys.argv[1:]
    else:
        (ns, args) = pre_parser.parse_known_args()
        if ns.command is not None:
            args = [ns.command, *args]
        else:
            for a in args[:]:
                if a in subparsers.choices:
                    args.remove(a)
                    args = [a, *args]
                    break
        if args[0] in ['-h', '--help']:
            args[0] = 'help'
    (ns, args_tmp) = parser.parse_known_args(args)
    args_dict = vars(ns)
    args_dict.update({'args': args_tmp})
    if args_dict['command'] is None:
        log.warning('Need command')
        log.info(info)
        return 1
    if args_dict['command'] in ('install') and args_dict['args']:
        cmd = args_dict['command']
        args_dict['command'] = 'brew'
        args_dict['args'].insert(0, cmd)

    b.set_args(**args_dict)

    if b.opt['command'] == 'help':
        log.info(parser.format_help())
        return 0
    if b.opt['command'] == 'brew':
        if args_tmp and args_tmp[0] in ['-h', '--help']:
            log.info(subparsers.choices[b.opt['command']].format_help())
            return 0
    elif 'help' in args_tmp:
        log.info(subparsers.choices[b.opt['command']].format_help())
        return 0
    elif b.opt['command'] == 'commands':
        commands = [
            'install',
            'brew',
            'init',
            'dump',
            'set_repo',
            'set_local',
            'pull',
            'push',
            'clean',
            'clean_non_request',
            'update',
            'edit',
            'cat',
            'casklist',
            'get_files',
            'commands',
            'version',
            'help',
        ]
        commands_hyphen = [
            '-i',
            '--init',
            '-s',
            '--set_repo',
            '--set_local',
            '-c',
            '--clean',
            '--clean_non_request',
            '-u',
            '--update',
            '-e',
            '--edit',
            '--cat',
            '--commands',
            '-v',
            '--version',
            '-h',
            '--help',
        ]
        options = [
            '-f',
            '--file',
            '-b',
            '--backup',
            '-F',
            '--format',
            '--form',
            '--leaves',
            '--on_request',
            '--top_packages',
            '-U',
            '--noupgrade',
            '-r',
            '--repo',
            '--fetch-HEAD',
            '-n',
            '--nolink',
            '--caskonly',
            '--appstore',
            '--no_appstore',
            '--all_files',
            '-d',
            '--dry_run',
            '-y',
            '--yes',
            '-V',
            '--verbose',
        ]
        log.info(
            f'commands: {" ".join(commands)}\n'
            f'commands_hyphen: {"".join(commands_hyphen)}\n'
            f'options: {" ".join(options)}',
        )
        return 0
    elif b.opt['command'] == 'version':
        b.helper.proc('brew -v', print_cmd=False)
        log.info(f'{__prog__} {__version__} {__date__}')
        return 0

    try:
        b.execute()
    except KeyboardInterrupt:
        return 1
    except CmdError as e:
        b.log.exception('')
        return e.return_code
    except RuntimeError:
        b.log.exception('')
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
