Brew-file
=========

[![Build Status](https://travis-ci.org/rcmdnk/homebrew-file.svg?branch=master)](https://travis-ci.org/rcmdnk/homebrew-file)

Manager for packages of Homebrew, inspired by [Brewdler](https://github.com/andrew/brewdler).

Renamed from brewall.

## Requirements

[Homebrew](https://github.com/mxcl/homebrew)

## Installation

By install script:

    $ curl -fsSL https://raw.github.com/rcmdnk/homebrew-file/install/install.sh |sh

This installs Homebrew if it has not been installed, too.

By Homebrew:

    $ brew tap rcmdnk/file
    $ brew install brew-file

Or download `bin/brew-file` and put it in anywhere under `PATH` (e.g. `~/usr/bin/`)

## Manage Brewfile with GitHub

Brew-file uses Brewfile, with which packages are managed.

With Brew-file, you can manage Brewfile with GitHub (or other server).

### Create a repository in GitHub with brew-file

You can create a repository with brew-file command:

    $ brew file set_repo

    Set repository, "non" for local Brewfile.
    <user>/<repo> for GitHub repository,
    or full path for the repository: 

Then give a name like `rcmdnk/Brewfile`, or `git@github.com:rcmdnk/Brewfile`.

If the repository doesn't exist, it enters a repository creation process.

### Prepare a repository in GitHub or other Git server.

Make GitHub repository named **Brewfile**,
and make one file named **Brewfile** in the repository.

You can make the initial Brewfile by yourself,
or can initialize Brewfile by Brew-file as written below.

## Usage

Brwe-file manages pakcages installed by Homebrew.
It also supports [brew-tap](https://github.com/mxcl/homebrew/wiki/brew-tap)
and [brew-cask](https://github.com/phinze/homebrew-cask).

It uses input file. By default, the file is `/usr/local/Library/Brewfile`.
You can reuse `Brewfile` for Brewdler, too.

If you want to specify input file, use `-f` option.

If you want to change default Brewfile, set environmental variable: HOMEBREW_BREWFILE
in your setup file (e.g. .bashrc), like:

    export HOMEBREW_BREWFILE=~/.brewfile

If there is no Brewfile, Brew-file ask you if you want to initialize Brewfile
with installed packages.
You can also make it with `-i` option.

If no argument is given, Brew-file tries to install packages listed in Brewfile.
If any packages managed with brew-cask are listed, brew-cask is also installed automatically.

Brewfile convention is similar as Brewdler.
Normally, you don't need to modify anything on Brewdler's Brewfile for Brew-file

Example:

    # Tap repositories and their packages
    tap 'caskroom/cask'
    install 'brew-cask'
    
    tapall 'rcmdnk/file' # This will trigger `brew install brew-file`, too
    
    # Cask packages
    cask install 'firefox'
    
    # Other Homebrew packages
    install 'mercurial'
    install 'macvim --with-lua'

First column is command: `brew`(or `install`)/`tap`/`tapall`/`cask`(or `cask install`.
Second to the last columns are package name and options.
They are used as arguments for such `brew install`,
therefore any options of Homebrew can be used.

For example, if you want to build macvim with lua, you can write as above.

If you use `tap`, Brew-file only does `tap` the repository.

If you use `tapall`, Brew-file does `brew install` for all Formulae in the repository
inaddition to do `tap` the repository.

You don't need to `brew install` by hand.
As written above, `tap 'caskroom/cask'` is can be dropped
because `cask 'firefox'` triggers it.

Some packages such macvim has Application (MacVim.app).
If you want to install them to Applications area,
please use `-l` (for `~/Applications/`) or `-g` (for `/Applications/`).

With `clean` option, Brew-file runs cleanup.
By default, it just does dry run (no actual cleanup).
To run cleanup in non dry-run mode, use `-C`.

If you want edit Brewfile, use `edit` option.

:warning: If you do `brew file edit` before installing Brewfile and save w/o any modification,
you may make empty Brewfile (Be careful, `brew -c -C` remove all packages :scream:).
Therefore I recommend you to do `brew file -i` at first if you don't have Brewfile.

You can maintain your Brewfile at the git repository.
First, make new repository at GitHub (or other git server).

Then, set the repository by:

    $ brew file set_repo -r <repository>

It will clone the repository.
If the repository has a file named "Brewfile", the file will be used instead of 
`/usr/local/Library/Brewfile`.
(then `/usr/local/Library/Brewfile` will have this repository informatoin.)

`repository` should be like [rcmdnk/Brewfile](https://github.com/rcmdnk/Brewfile) in GitHub,
which should have "Brewfile" (different file name can be used by `-f`).

If you want to use other hosts than github, use full path for the repository, like

    $ brew file set_repo -r git@bitbucket.org:rcmdnk/my_brewfile

If the repository doesn't have "Brewfile"(or specified by `-f`, `brew file init` initialize the file.
Then, you can push it by `brew file push`.

With this procedure, you can synchronize all your Mac easily :thumbsup:

To install new package, use

    $ brew file brew intall <package>

instead of `brew install <package>`, because above command
automatically update Brewfile.

This is useful especially if you are using the repository for the Brewfile,
and want to use `brew file update`.

Otherwise, please be careful to use `brew file update`,
because it deletes what you installed, but you have not registered in Brewfile.

If you want to check your Apps in `/Applications`, `/Applications/Utilities` or `~/Applications/`
for Cask, use:

    $ brew file casklist

This command makes `Caskfile.txt`, which is like:

    ### Cask applications
    ### Please copy these lines to your Brewfile and use with `brew bundle`.
    
    ### tap and install Cask (remove comment if necessary).
    #tap caskroom/cask
    #install brew-cask
    
    ### Apps installed by Cask in /Applications
    cask install adobe-reader # /Applications/Adobe Reader.app
    cask install xtrafinder # /Applications/XtraFinder.app
    
    ### Apps installed by Cask in /Applications/Utilities:
    cask install xquartz # /Applications/Utilities/XQuartz.app
    
    ### Apps installed by Cask in ~/Applications.
    cask install bettertouchtool.rb # ~/Applications/BetterTouchTool.app
    
    #############################
    
    ### Apps not installed by Cask, but installed in /Applications.
    ### If you want to install them with Cask, remove comments.
    #cask install keyremap4macbook # /Applications/KeyRemap4MacBook.app
    
    ### Apps not installed by Cask, but installed in /Applications/Utilities:
    ### If you want to install them with Cask, remove comments.

    ### Apps not installed by Cask, but installed in ~/Applications.
    ### If you want to install them with Cask, remove comments.
    #cask install copy.rb # ~/Applications/Copy.app
    
    
    #############################
    
    ### Apps not registered in Cask, but installed in /Applications.
    # /Applications/App Store.app
    # /Applications/Calendar.app
    ...
    
    ### Apps not registered in Cask, but installed in /Applications/Utilities:
    ...
    
    ### Apps not registered in Cask, but installed in ~/Applications.

You can find applications which were installed manually,
but can be managed by Cask under "Apps not installed by Cask, but installed in...".

If you want to manage them with Brewfile, just copy above lines w/o "#" for these Apps.

# HELP

    Usage: brew file [-increvh][-f <input file>] command ...

    Commands:
      install            : Install packages in BREWFILE (do 'brew update', too).
      brew [command ...] : Execute brew command, and update BREWFILE.
      init     (or -i)   : Initialize/Update BREWFILE with installed packages.
      brew noinit [command ...] : Execute brew command, w/o update of BREWFILE.
      set_repo (or -s)   : Set BREWFILE repository.
      pull               : Update BREWFILE from the repository.
      push               : Push your BREWFILE to the repository.
      clean    (or -c)   : Clenup
                                   Uninstall packages not in the list.
                                   Untap packages not in the list.
                                   Cleanup cache (brew cleanup)
                                   By drault, cleanup runs as dry-run.
                                   If you want to enforce cleanup, use '-C' option.
      update   (or -u)   : Do pull, install, brew upgrade, push and clean -C.
                                   pull, push and clean are done only if
                                   the repository is assigned.
      edit     (or -e)   : Edit input file.
      casklist           : Check applications for Cask
      version  (or -v)   : Show version.
      help     (or -h)   : Print Help (this message) and exit.
    
    Options:
          -f  <file> Set input file (current default: ${input})
                     You can set input file by environmental variable,
                     HOMEBREW_BREWFILE, like:
                          export HOMEBREW_BREWFILE=~/.brewfile
          -n         Don't make links for Apps
          -C         Run cleanup in non dry-run mode.
          -r  <repo> Set repository name. Use with set_repo (-s).
    
    If you want to use repository's BREWFILE,
    please prepare a repository which has a file named 'Brewfile'.
    If you assign the repository which doesn't have 'Brewfile',
    then Brew-file will try to make 'Brewfile' in the repository.
    For GitHub repository, you can shorten the address like user_name/repo_name.

## Information
More information could be found in [my blog](http://rcmdnk.github.io/blog/2013/09/13/computer-mac-install-homebrew/).

> [Brewall: brewパッケージを管理する](http://rcmdnk.github.io/blog/2013/09/13/computer-mac-install-homebrew/)

> [brew-file: Brewfileを扱うbrewallを改名した](http://rcmdnk.github.io/blog/2014/08/26/computer-mac-homebrew/)

# brew-wrap

If you want to automatically update Brewfile after `brew install/uninstall`,
please use `brew-wrap`.

You can use it by set as alias:

    if type brew >& /dev/null && type brew-file >& /dev/null && type brew-wrap >& /dev/null;then
      alias brew="brew-wrap"
    fi

Write it in your setting file like `.bashrc`.


