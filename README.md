Brewall
=======

Manager for packages of Homebrew, inspired by [Brewdler](https://github.com/andrew/brewdler).

## Requirements

[Homebrew](https://github.com/mxcl/homebrew)

## Installation

By Homebrew:

    $ brew tap rcmdnk/brewall

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

    brew 'mercurial'
    brew 'macvim --with-lua'
    tap 'phinze/cask'
    cask 'firefox'

First column is command: `brew`/`tap`/`cask`.
Second to the last columns are package name and options.
They are used as arguments for such `brew install`,
therefore any options of Homebrew can be used.

For example, if you want to build macvim with lua, you can write as above.

If you use `tap`, Brewall do `tap` and `brew install`, too.
You don't need to `brew install` by hand.
As written above, `tap 'phinze/cask'` is can be dropped
because `cask 'firefox'` triggers it.

Some packages such macvim has Application (MacVim.app).
If you want to install them to Applications area,
please use `-l` (for `~/Applications/`) or `-g` (for `/Applications/`).

With `-c` option, Brewall runs cleanup.
By default, it just does dry run (no actual cleanup).
To run cleanup in non dry-run mode, use `-r`.

If you want edit Brewfile, use `-e` option.

:warning: If you do `brewall -e` before installing Brewfile and save w/o any modification,
you may make empty Brewfile (Be careful, `brew -c -r` remove all packages :scream:).
Therefore I recommend you to do `brewall -i` at first if you don't have Brewfile.

    Usage: brewall [-cerieh][-f <input file>]

    Arguments:
          -f  <file> Set input file (current default: /usr/local/Library/Brewfile)
                     You can set input file by environmental variable,
                     HOMEBREW_BREWFILE, like:
                          export HOMEBREW_BREWFILE=~/.brewfile
          -l         Make links to apps (for such MacVim)
                     The default place is user's directory: ~/Applications/
                     If you want to install in global directory: /Applications/,
                     use '-g'
          -g         Make apps' links in /Applications/ (need root password)
          -c         Cleanup:
                       Uninstall packages not in the list.
                       Untap packages not in the list.
                       Cleanup cache (brew cleanup)
                     By drault, cleanup runs as dry-run.
                     If you want to enforce cleanup, use '-r' option.
          -r         Run cleanup in non dry-run mode.
          -i         Initialize Brewfile with insalled packages.
          -e         Edit input file
          -h         Print Help (this message) and exit

## Information
More information could be found in [my blog (Japanese)](http://rcmdnk.github.io/blog/2013/09/13/computer-mac-install-homebrew/).
