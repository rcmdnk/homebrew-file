Brewall
=======

Manager for packages of Homebrew, inspired by [Brewdler](https://github.com/andrew/brewdler).

## Requirements

[Homebrew](https://github.com/mxcl/homebrew)

## Installation

By install script:

    $ curl -fsSL https://raw.github.com/rcmdnk/brewall/install |sh

This installs Homebrew if it has not been installed, too.

By Homebrew:

    $ brew tap rcmdnk/brewall
    $ brew install brewall

Or download `bin/brewall` and put it in anywhere under `PATH` (e.g. `~/usr/bin/`)

## Usage
Brewall manages pakcages installed by Homebrew.
It also supports [brew-tap](https://github.com/mxcl/homebrew/wiki/brew-tap)
and [brew-cask](https://github.com/phinze/homebrew-cask).

It uses input file. By default, the file is `/usr/local/Library/Brewfile`.
You can reuse `Brewfile` for Brewdler, too.

If you want to specify input file, use `-f` option.

If you want to change default Brewfile, set environmental variable: HOMEBREW_BREWFILE
in your setup file (e.g. .bashrc), like:

    export HOMEBREW_BREWFILE=~/.brewfile

If there is no Brewfile, Brewall ask you if you want to initialize Brewfile
with installed packages.
You can also make it with `-i` option.

If no argument is given, Brewall tries to install packages listed in Brewfile.
If any packages managed with brew-cask are listed, brew-cask is also installed automatically.

Brewfile convention is similar as Brewdler.
Normally, you don't need to modify anything on Brewdler's Brewfile for Brewall.

Example:

    # Tap repositories and their packages
    tap 'caskroom/cask'
    install 'brew-cask'
    
    tapall 'rcmdnk/brewall' # This will trigger `brew 'brewall'`, too
    
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

If you use `tap`, Brewall only does `tap` the repository.

If you use `tapall`, Brewall does `brew install` for all Formulae in the repository
inaddition to do `tap` the repository.

You don't need to `brew install` by hand.
As written above, `tap 'caskroom/cask'` is can be dropped
because `cask 'firefox'` triggers it.

Some packages such macvim has Application (MacVim.app).
If you want to install them to Applications area,
please use `-l` (for `~/Applications/`) or `-g` (for `/Applications/`).

With `clean` option, Brewall runs cleanup.
By default, it just does dry run (no actual cleanup).
To run cleanup in non dry-run mode, use `-C`.

If you want edit Brewfile, use `edit` option.

:warning: If you do `brewall edit` before installing Brewfile and save w/o any modification,
you may make empty Brewfile (Be careful, `brew -c -C` remove all packages :scream:).
Therefore I recommend you to do `brewall -i` at first if you don't have Brewfile.

You can maintain your Brewfile at the git repository.
First, make new repository at GitHub (or other git server).

Then, set the repository by:

    $ brewall set_repo -r <repository>

It will clone the repository.
If the repository has a file named "Brewfile", the file will be used instead of 
`/usr/local/Library/Brewfile`.
(then `/usr/local/Library/Brewfile` will have this repository informatoin.)

If the repository doesn't have "Brewfile", `brewall init` initialize the file.
Then, you can push it by `brewall push`.

With this procedure, you can synchronize all your Mac easily :thumbsup:

To install new package, use

    $ brewall brew intall <package>

instead of `brew install <package>`, because above command
automatically update Brewfile.

This is useful especially if you are using the repository for the Brewfile,
and want to use `brewall update`.

Otherwise, please be careful to use `brewall update`,
because it deletes what you installed, but you have not registered in Brewfile.

If you want to check your Apps in `/Applications` or `~/Applications/`
for Cask, use:

    $ brewall casklist

This command makes `Caskfile.txt`, which is like:

    ### Cask applications
    ### Please copy these lines to your Brewfile and use with `brew bundle`.
    
    ### tap and install Cask (remove comment if necessary).
    #tap caskroom/cask
    #install brew-cask
    
    ### Apps installed by Cask in /Applications
    cask install adobe-reader # /Applications/Adobe Reader.app
    cask install xtrafinder # /Applications/XtraFinder.app
    
    ### Apps installed by Cask in ~/Applications.
    cask install bettertouchtool.rb # ~/Applications/BetterTouchTool.app
    
    #############################
    
    ### Apps not installed by Cask, but installed in /Applications.
    ### If you want to install them with Cask, remove comments.
    #cask install keyremap4macbook # /Applications/KeyRemap4MacBook.app
    
    ### Apps not installed by Cask, but installed in ~/Applications.
    ### If you want to install them with Cask, remove comments.
    #cask install copy.rb # ~/Applications/Copy.app
    
    
    #############################
    
    ### Apps not registered in Cask, but installed in /Applications.
    # /Applications/App Store.app
    # /Applications/Calendar.app
    ...
    
    ### Apps not registered in Cask, but installed in ~/Applications.

You can find applications which were installed manually,
but can be managed by Cask under "Apps not installed by Cask, but installed in...".

If you want to manage them with Brewfile, just copy above lines w/o "#" for these Apps.

# HELP

    Usage: brewall [-increvh][-f <input file>] command ...

    Commands:
      brewall install            : Install packages in BREWFILE (do 'brew update', too).
      brewall brew [command ...] : Execute brew command, and update BREWFILE.
      brewall init     (or -i)   : Initialize/Update BREWFILE with installed packages.
      brewall set_repo (or -s)   : Set BREWFILE repository.
      brewall pull               : Update BREWFILE from the repository.
      brewall push               : Push your BREWFILE to the repository.
      brewall clean    (or -c)   : Clenup
                                   Uninstall packages not in the list.
                                   Untap packages not in the list.
                                   Cleanup cache (brew cleanup)
                                   By drault, cleanup runs as dry-run.
                                   If you want to enforce cleanup, use '-C' option.
      brewall update   (or -u)   : Do pull, install, brew upgrade, push and clean -C.
                                   pull, push and clean are done only if
                                   the repository is assigned.
      brewall edit     (or -e)   : Edit input file.
      brewall casklist           : Check applications for Cask
      brewall version  (or -v)   : Show version.
      brewall help     (or -h)   : Print Help (this message) and exit.
    
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
    then brewall will try to make 'Brewfile' in the repository.
    For GitHub repository, you can shorten the address like user_name/repo_name.

## Information
More information could be found in [my blog](http://rcmdnk.github.io/blog/2013/09/13/computer-mac-install-homebrew/).


[![Bitdeli Badge](https://d2weczhvl823v0.cloudfront.net/rcmdnk/homebrew-brewall/trend.png)](https://bitdeli.com/free "Bitdeli Badge")

