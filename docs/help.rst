Help
====

Help message of brew-file:

.. code-block:: none

    usage: brew-file [-f INPUT] [-b BACKUP] [-F FORM] [--leaves] [--on-request]
                     [--top-packages TOP_PACKAGES] [--full-name] [-U] [-r REPO]
                     [--no-repo] [--fetch-HEAD] [-n] [--caskonly]
                     [--appstore APPSTORE] [--no-appstore] [--desc] [-d] [-y]
                     [-V {debug,info,warning,error,critical}] [-h]
                     [command] ...

    Brew-file: Manager for packages of Homebrew.

    https://github.com/rcmdnk/homebrew-file

    requirement: Python 3.9.0 or later

    options:
      -f, --file INPUT      Set input file (default: ~/.config/brewfile/Brewfile). You can set input file by environmental variable, HOMEBREW_BREWFILE, like:
                                export HOMEBREW_BREWFILE=~/.brewfile
      -b, --backup BACKUP   Set backup file (default: ). If it is empty, no backup is made. You can set backup file by environmental variable, HOMEBREW_BREWFILE_BACKUP, like:
                                export HOMEBREW_BREWFILE_BACKUP=~/brewfile.backup
      -F, --format, --form FORM
                            Set input file format (default: None).
                            file (or none)    : brew vim --HEAD --with-lua
                            brewdler or bundle: brew 'vim', args: ['with-lua', 'HEAD']
                              Compatible with [homebrew-bundle](https://github.com/Homebrew/homebrew-bundle).
                            command or cmd    : brew install vim --HEAD --with-lua
                              Can be used as a shell script.
      --leaves              Make list only for leaves (taken by `brew leaves`). You can set this by environmental variable, HOMEBREW_BREWFILE_LEAVES, like:
                                export HOMEBREW_BREWFILE_LEAVES=1
      --on-request, --on_request
                            Make list only for packages installed on request. This option is given priority over 'leaves'. You can set this by environmental variable, HOMEBREW_BREWFILE_ON_REQUEST, like:
                                export HOMEBREW_BREWFILE_ON_REQUEST=1
      --top-packages, --top_packages TOP_PACKAGES
                            Packages to be listed even if they are under dependencies and `leaves`/'on_request' option is used. You can set this by environmental variable, HOMEBREW_BREWFILE_TOP_PACKAGES (',' separated), like:
                                export HOMEBREW_BREWFILE_TOP_PACKAGES=go,coreutils
      --full-name, --full_name
                            Use full names (tap/package) for packages. You can set this by environmental variable, HOMEBREW_BREWFILE_FULL_NAME, like:
                                export HOMEBREW_BREWFILE_FULL_NAME=1
      -U, --noupgrade       Do not execute `brew update/brew upgrade` at `brew file update`.
      -r, --repo REPO       Set repository name. Use with set_repo.
      --no-repo, --no_repo  Do not ask if setting repository when initialize Brewfile.
      --fetch-HEAD, --fetch_HEAD
                            Fetch HEAD at update.
      -n, --nolink          Don't make links for Apps.
      --caskonly            Write out only cask related packages
      --appstore APPSTORE   Set AppStore application check level.
                            0: do not check,
                            1: check and manage,
                            2: check for installation, but do not add to Brewfile when Apps are added. You can set the level by environmental variable:
                                export HOMEBREW_BREWFILE_APPSTORE=0
      --no-appstore, --no_appstore
                            Set AppStore application check level to 0. (legacy option, works same as '--appstore 0'.)
      --desc, --describe    Add a description comment for each package. You can set this by environmental variable, HOMEBREW_BREWFILE_DESCRIBE, like:
                                export HOMEBREW_BREWFILE_DESCRIBE=1
      -d, --dry-run, --dry_run
                            Set dry run mode.
      -y, --yes             Answer yes to all yes/no questions.
      -V, --verbose {debug,info,warning,error,critical}
                            Verbose level
      -h, --help            Print Help (this message) and exit.

    subcommands:
      [command]
        install             Install packages in BREWFILE if no <package> is given. If <package> is given, the package is installed and it is added in BREWFILE.
        brew                Execute brew command, and update BREWFILE. Use 'brew noinit <brew command>' to suppress Brewfile initialization.
        init                or dump/-i/--init
                            Initialize/Update BREWFILE with installed packages.
        set_repo            or -s/--set_repo
                            Set BREWFILE repository (e.g. rcmdnk/Brewfile or full path to your repository).
        set_local           or --set_local
                            Set BREWFILE to local file.
        pull                Update BREWFILE from the repository.
        push                Push your BREWFILE to the repository.
        clean               or -c/--clean
                            Cleanup. Uninstall packages not in the list. Untap packages not in the list. Cleanup cache (brew cleanup and delete rm -rf $(brew --cache)).
        clean_non_request   or --clean_non_request.
                            Uninstall packages which were installed as dependencies but parent packages of which were already uninstalled (same as `brew autoremove`).
        update              or -u/--update
                            Do brew update/upgrade, cask upgrade, pull, install, init and push. In addition, pull and push will be done if the repository is assigned.
                            It will enforce the state recorded in the Brewfile, potentially removing packages installed without `brew-wrap`. If you want to keep all packages in the system, you should better to run `brew file init` before running `brew file update`.
        edit                or -e/--edit
                            Edit input files.
        cat                 or --cat
                            Show contents of input files.
        casklist            Check applications for Cask.
        get_files           Get Brewfile's full path, including additional files.
        commands            or --commands
                            Show commands.
        version             or -v/--version
                            Show version.
        help                or -h/--help
                            Print Help (this message) and exit.

    Check https://homebrew-file.readthedocs.io for more details.
