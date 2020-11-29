Help
====

Help message of brew-file:

.. code-block:: none

    usage: brew-file [-f INPUT] [-b BACKUP] [-F FORM] [--leaves] [--on_request]
                     [--top_packages TOP_PACKAGES] [-U] [-r REPO] [-n]
                     [--caskonly] [--appstore APPSTORE] [--no_appstore] [-C] [-y]
                     [-V VERBOSE] [-h]
                     [command] ...

    Brew-file: Manager for packages of Homebrew
    https://github.com/rcmdnk/homebrew-file

    requirement: Python 3.7 or later

    optional arguments:
      -f INPUT, --file INPUT
                            Set input file (default: ~/.config/brewfile/Brewfile).
                            You can set input file by environmental variable,
                            HOMEBREW_BREWFILE, like:
                                export HOMEBREW_BREWFILE=~/.brewfile
      -b BACKUP, --backup BACKUP
                            Set backup file (default: ).
                            If it is empty, no backup is made.
                            You can set backup file by environmental variable,
                             HOMEBREW_BREWFILE_BACKUP, like:
                                export HOMEBREW_BREWFILE_BACKUP=~/brewfile.backup
      -F FORM, --format FORM, --form FORM
                            Set input file format (default: none).
                            file (or none)    : brew vim --HEAD --with-lua
                            brewdler or bundle: brew 'vim', args: ['with-lua', 'HEAD']
                              Compatible with [homebrew-bundle](https://github.com/Homebrew/homebrew-bundle).
                            command or cmd    : brew install vim --HEAD --with-lua
                              Can be used as a shell script.
      --leaves              Make list only for leaves (taken by `brew leaves`).
                            You can set this by environmental variable, HOMEBREW_BREWFILE_LEAVES, like:
                                export HOMEBREW_BREWFILE_LEAVES=1
      --on_request          Make list only for packages installed on request.
                            This option is given priority over 'leaves'.
                            You can set this by environmental variable, HOMEBREW_BREWFILE_ON_REQUEST, like:
                                export HOMEBREW_BREWFILE_ON_REQUEST=1
      --top_packages TOP_PACKAGES
                            Packages to be listed even if they are under dependencies
                            and `leaves`/'on_request' option is used.
                            You can set this by environmental variable,
                             HOMEBREW_BREWFILE_TOP_PACKAGES (',' separated), like:
                                export HOMEBREW_BREWFILE_TOP_PACKAGES=go,coreutils
      -U, --noupgrade       Do not execute `brew update/brew upgrade` at `brew file update`.
      -r REPO, --repo REPO  Set repository name. Use with set_repo.
      -n, --nolink          Don't make links for Apps.
      --caskonly            Write out only cask related packages
      --appstore APPSTORE   Set AppStore application check level.
                            0: do not check,
                            1: check and manage,
                            2: check for installation,but do not add to Brewfile when Apps are added.
                            You can set the level by environmental variable:
                                export HOMEBREW_BREWFILE_APPSTORE=0
      --no_appstore         Set AppStore application check level to 0.
                            (legacy option, works same as '--appstore 0'.)
      -C                    Run clean as non dry-run mode.
                            Use this option to run clean at update command, too.
      -y, --yes             Answer yes to all yes/no questions.
      -V VERBOSE, --verbose VERBOSE
                            Verbose level 0/1/2
      -h, --help            Print Help (this message) and exit.

    subcommands:
      [command]
        install             Install packages in BREWFILE if no <package> is given.
                            If <package> is given, the package is installed and it is added
                            in BREWFILE.
        brew                Execute brew command, and update BREWFILE.
                            Use 'brew noinit <brew command>' to suppress Brewfile initialization.
        init                or dump/-i/--init
                            Initialize/Update BREWFILE with installed packages.
        set_repo            or -s/--set_repo
                            Set BREWFILE repository (e.g. rcmdnk/Brewfile or full path to your repository).
        set_local           or --set_local
                            Set BREWFILE to local file.
        pull                Update BREWFILE from the repository.
        push                Push your BREWFILE to the repository.
        clean               or -c/--clean
                            Cleanup.
                            Uninstall packages not in the list.
                            Untap packages not in the list.
                            Cleanup cache (brew cleanup)
                            By default, cleanup runs as dry-run.
                            If you want to enforce cleanup, use '-C' option.
        clean_non_request   or --clean_non_request.
                            Uninstall packages which were installed as dependencies
                            but parent packages of which were already uninstalled.
                            By default, cleanup runs as dry-run.
                            If you want to enforce cleanup, use '-C' option.
        update              or -u/--update
                            Do brew update/upgrade, cask upgrade, pull,install,
                            init and push.
                            In addition, pull and push
                            will be done if the repository is assigned.
                            'clean' is also executed after install if you give -C option.
        edit                or -e/--edit
                            Edit input files.
        cat                 or --cat
                            Show contents of input files.
        casklist            Check applications for Cask.
        test                or --test. Used for test.
        get_files           Get Brewfile's full path, including additional files.
        commands            or --commands
                            Show commands.
        version             or -v/--version
                            Show version.
        help                or -h/--help
                            Print Help (this message) and exit.

    Check https://homebrew-file.readthedocs.io for more details.
