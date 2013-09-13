brewall
=======

Manager for packages of Homebrew

## Requirements

[Homebrew](https://github.com/mxcl/homebrew)

## Installation

By Homebrew:

    $ brew tap rcmdnk/brewall

Or download `bin/brewall` and put it in anywhere you want (e.g. `~/usr/bin/`)

## Usage

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
                     If you want to enforce cleanup, use '-e' option.
          -r         Run cleanup in non dry-run mode.
          -i         Initialize Brewfile with insalled packages.
          -e         Edit input file
          -h         Print Help (this message) and exit
    
