Brew-file
=========

[![Build Status](https://travis-ci.org/rcmdnk/homebrew-file.svg?branch=master)](https://travis-ci.org/rcmdnk/homebrew-file)
[![Coverage Status](https://coveralls.io/repos/rcmdnk/homebrew-file/badge.png?branch=master)](https://coveralls.io/r/rcmdnk/homebrew-file?branch=master)

Manager for packages of Homebrew, inspired by [Brewdler](https://github.com/andrew/brewdler)
(Renamed from brewall).

Brewfile dumped by [homebrew-brewdler](https://github.com/Homebrew/homebrew-brewdler)
can be used as input, too.


## Update

### 28/Sep/2014

Master branch was switched to python version from bash version.

If you have already installed brew-file with Homebrew,
please uninstall, and untap brew-file, and install again:

    $ brew uninstall brew-file
    $ command brew untap rcmdnk/file
    $ command brew install rcmdnk/file/brew-file

## Requirements

* [Homebrew](https://github.com/mxcl/homebrew) (Can be installed by the install script of brew-file, too).

* Python 2.7.7 or later (optional).

Although it is not mandatory,
the latest Python 2.7.X or 3.X is recommended,
to use `brew file brew` command (and `brew-wrap`).

If you've not installed, pip, first install pip:

    $ easy_install pip

Then, install python by Homebrew (after installing it):

    $ brew install python

or

    $ brew install python3


> [Can’t ignore unknown argument in subparser of ArgumentParser of Python even if parse_known_args is given](http://rcmdnk.github.io//en/blog/2015/03/08/computer-python/)

> [PythonのArgumentParserでsubparserを使うとparse_known_argsでもunknownな引数が無視できないエラーについて](http://rcmdnk.github.io/blog/2014/12/25/computer-python/)

## Installation

By install script:

    $ curl -fsSL https://raw.github.com/rcmdnk/homebrew-file/install/install.sh |sh

This installs Homebrew if it has not been installed, too.

By Homebrew:

    $ brew install rcmdnk/file/brew-file

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

To create a repository,
you need [Requests](http://docs.python-requests.org/en/latest/) module.

To install **Requests**, do:

    $ easy_install pip # in case you've not installed pip
    $ pip install requests

### Prepare a repository in GitHub or other Git server.

Make a repository with a file named **Brewfile** in GitHub or other Git server.

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

You can also modify the default installation locations of Cask packages.
To make this settings, it is the same as issuing [How to Use Homebrew-cask#Options](https://github.com/caskroom/homebrew-cask/blob/master/USAGE.md#options).
you might want to add the following line to your .bash_profile or .zshenv:

    export HOMEBREW_CASK_OPTS="--caskroom=/etc/Caskroom --appdir=$HOME/MyApplications"

If there is no Brewfile, Brew-file ask you if you want to initialize Brewfile
with installed packages.
You can also make it with `-i` option.

If no argument is given, Brew-file tries to install packages listed in Brewfile.
If any packages managed with brew-cask are listed, brew-cask is also installed automatically.

Brewfile convention is similar as Brewdler.
Normally, you don't need to modify anything on Brewdler's Brewfile for Brew-file

Example:

    # Tap repositories and their packages
    tap caskroom/cask
    brew 'brew-cask'
    # install brew-cask # install is same as "brew". Quotes are not mandatory.
    
    tapall rcmdnk/file # This will trigger `brew install brew-file`, too
    
    # Cask packages
    cask firefox
    #cask install firefox # "cask install" is same as "cask"
    
    # Other Homebrew packages
    brew mercurial
    brew macvim --with-lua

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

If you want to check your Apps for Cask, use:

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

## HELP


    usage: brew file [-f INPUT] [-r REPO] [-n] [-C] [-V VERBOSE] [command] ...
    
    Brew-file: Manager for packages of Homebrew
    https://github.com/rcmdnk/homebrew-file
    
    optional arguments:
      -f INPUT, --file INPUT
                            Set input file (default: /usr/local/Library/Brewfile).
                            You can set input file by environmental variable,
                            HOMEBREW_BREWFILE, like:
                                export HOMEBREW_BREWFILE=~/.brewfile
      -F FORMAT, --format FORMAT
                            Set input file format (default: file).
                            file:     brew vim --HEAD --with-lua
                            brewdler: brew 'vim', args: ['with-lua', 'HEAD']
      -r REPO, --repo REPO  Set repository name. Use with set_repo.
      -n, --nolink          Don't make links for Apps.
      -C                    Run cleanup in non dry-run mode.
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
                            Do pull, install, brew update/upgrade, init,
                            push and clean -C.
                            In addition, pull, push and clean
                            will be done if the repository is assigned.
        edit                or -e/--edit
                            Edit input file.
        casklist            Check applications for Cask.
        cask_upgrade        Upgrade cask applications.
                            With -C, old versions will be removed.
        test                Used for test.
        version             or -v/--version
                            Show version.
        help                or -h/--help
                            Print Help (this message) and exit.


## Information
More information could be found in
my blogs: [Japanese](http://rcmdnk.github.io/), [English](http://rcmdnk.github.io/en/)

> [Brewall: brewパッケージを管理する](http://rcmdnk.github.io/blog/2013/09/13/computer-mac-install-homebrew/) (jp)

> [brew-file: Brewfileを扱うbrewallを改名した](http://rcmdnk.github.io/blog/2014/08/26/computer-mac-homebrew/) (jp)

> [Brew-file: Manager for packages of Homebrew](http://rcmdnk.github.io/en/blog/2014/11/15/computer-mac-homebrew/) (en)

## brew-wrap

If you want to automatically update Brewfile after `brew install/uninstall`,
please use `brew-wrap`.

[homebrew-file/etc/brew-wrap](https://github.com/rcmdnk/homebrew-file/blob/master/etc/brew-wrap)
has a wrapper function `brew`.

Features:

* It executes `brew file init` after such `brew install` automatically.
* `file` can be skipped for non-conflicted commands with `brew`.  :new: 09/May/2015
    * e.g.) `init` command is not in `brew`. Then, you can replace `brew file init` with:

            $ brew init

    * Such `edit` command is also in `brew`. In this case, `brew edit`
    executes original `brew edit`.
        * But you can use `brew -e` or `brew --edit` to edit **Brewfile**.

To enable it, just read this file in your `.bashrc` or any of your setup file.

```sh
if [ -f $(brew --prefix)/etc/brew-wrap ];then
  source $(brew --prefix)/etc/brew-wrap
fi
```

`brew` function in `brew-wrap` executes original `brew`
if `brew-file` is not included.

Therefore, you can safely uninstall/re-install brew-file
even if you have already sourced it.

Some subcommands of `brew-file` can be used
as a subcommand of `brew`, if the command is not in original brew subcommands.

Such `init` or `casklist` commands can be used like:

    $ brew init # = brew file init

    $ brew casklist # brew file casklist

With completion settings below,
`file` is included in the completion list of `brew`.

In addition, the completion for `brew file` is also enabled,
as same as `brew-file` command.

:warning:

Previously, `brew-wrap` was in `bin/brew-wrap`,
and it was used like `alias brew="brew-wrap"`.

If you have this obsolete setting, please delete and renew as above.

## Completion

Functions for Bash/Zsh completions are also installed.

For Bash, please install
[Bash-Completion](http://bash-completion.alioth.debian.org/)
by:

    $ brew install bash-completion

then, add following settings to your **.bashrc**:

```sh
brew_completion=$(brew --prefix 2>/dev/null)/etc/bash_completion
if [ $? -eq 0 ] && [ -f "$brew_completion" ];then
  source $brew_completion
fi
```

For Zsh, add following settings in your **.zshrc**:

```sh
brew_completion=$(brew --prefix 2>/dev/null)/share/zsh/zsh-site-functions
if [ $? -eq 0 ] && [ -d "$brew_completion" ];then
  fpath=($brew_completion $fpath)
fi
autoload -U compinit
compinit
```

In case you have installed [zsh-completions](https://github.com/zsh-users/zsh-completions)
 (can be installed by brew: `$ brew install zsh-completions`)、
settings can be like:

```sh
for d in "/share/zsh-completions" "/share/zsh/zsh-site-functions";do
  brew_completion=$(brew --prefix 2>/dev/null)$d
  if [ $? -eq 0 ] && [ -d "$brew_completion" ];then
    fpath=($brew_completion $fpath)
  fi
done
autoload -U compinit
compinit
```

If you are using `brew-wrap`, please write these completion settings
**BEFORE** `brew-wrap` reading.
