Help
====

Help message of brew-file:

.. code-block:: none

   usage: brew-file [-f INPUT] [-b BACKUP] [-F FORM] [-U] [--preupdate] [-r REPO]
                    [-n] [--caskonly] [--no_appstore] [-C] [-y] [-V VERBOSE]
                    [command] ...
   
   Brew-file: Manager for packages of Homebrew
   https://github.com/rcmdnk/homebrew-file
   
   requirement: Python 2.7 or later
   
   optional arguments:
     -f INPUT, --file INPUT
                           Set input file (default: /Users/user/.brewfile/Brewfile). 
                           You can set input file by environmental variable,
                           HOMEBREW_BREWFILE, like:
                               export HOMEBREW_BREWFILE=~/.brewfile
     -b BACKUP, --backup BACKUP
                           Set backup file (default: ). 
                           You can set input file by environmental variable, HOMEBREW_BREWFILE_BACKUP.
     -F FORM, --format FORM, --form FORM
                           Set input file format (default: file). 
                           file              : brew vim --HEAD --with-lua
                           brewdler or bundle: brew 'vim', args: ['with-lua', 'HEAD']
                             Compatible with [homebrew-bundle](https://github.com/Homebrew/homebrew-bundle).
                           command or cmd    : brew install vim --HEAD --with-lua
                             Can be used as a shell script.
     -U, --noupdate        Do not execute `brew update/brew upgrade` at `brew file update`.
     --preupdate           Execute `brew update` before install or other commands.
     -r REPO, --repo REPO  Set repository name. Use with set_repo.
     -n, --nolink          Don't make links for Apps.
     --caskonly            Write out only cask related packages
     --no_appstore         Don't check AppStore applications.
                           (For other than casklist command)
     -C                    Run cleanup in non dry-run mode.
     -y, --yes             Answer yes to all yes/no questions.
     -V VERBOSE, --verbose VERBOSE
                           Verbose level 0/1/2
   
   subcommands:
     [command]
       install             Install packages in BREWFILE.
                           Use `--preupdate` to execute `brew update` before install.
       brew                Execute brew command, and update BREWFILE.
       init                or dump/-i/--init
                           Initialize/Update BREWFILE with installed packages.
       set_repo            or -s/--set_repo
                           Set BREWFILE repository (e.g. rcmdnk/Brewfile).
       pull                Update BREWFILE from the repository.
       push                Push your BREWFILE to the repository.
       clean               or -c/--clean
                           Cleanup.
                           Uninstall packages not in the list.
                           Untap packages not in the list.
                           Cleanup cache (brew cleanup)
                           By drault, cleanup runs as dry-run.
                           If you want to enforce cleanup, use '-C' option.
       update              or -u/--update
                           Do pull, install, clean, brew update/upgrade,
                           init and push.
                           In addition, pull and push
                           will be done if the repository is assigned.
       edit                or -e/--edit
                           Edit input files.
       cat                 or --cat
                           Show contents of input files.
       casklist            Check applications for Cask.
       cask_upgrade        Check updates of cask applications.
                           With -C, upgrade is enforced (old versions will be removed).
       test                or --test. Used for test.
       get_files           Get Brewfile's full path, including additional files.
       commands            or --commands
                           Show commands.
       version             or -v/--version
                           Show version.
       help                or -h/--help
                           Print Help (this message) and exit.
