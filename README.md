Brew-file
=========

[![Build Status](https://travis-ci.org/rcmdnk/homebrew-file.svg?branch=master)](https://travis-ci.org/rcmdnk/homebrew-file)
[![Coverage Status](https://coveralls.io/repos/rcmdnk/homebrew-file/badge.png?branch=master)](https://coveralls.io/r/rcmdnk/homebrew-file?branch=master)

Manager for packages of Homebrew, inspired by [Brewdler](https://github.com/andrew/brewdler)
(Renamed from brewall).

Brewfile dumped by [homebrew-brewdler](https://github.com/Homebrew/homebrew-brewdler)
can be used as input, too.


## Installation

By install script:

    $ curl -fsSL https://raw.github.com/rcmdnk/homebrew-file/install/install.sh |sh

This installs Homebrew if it has not been installed, too.

By Homebrew:

    $ brew install rcmdnk/file/brew-file

Or download `bin/brew-file` and put it in anywhere under `PATH` (e.g. `~/usr/bin/`)


Then, add following lines in you **.bashrc** or **.zshrc** to wrap `brew` command:

```sh
if [ -f $(brew --prefix)/etc/brew-wrap ];then
  source $(brew --prefix)/etc/brew-wrap
fi
```

**brew-wrap** wraps original `brew` command
for an automatic update of Brewfile when you execute
such `brew install` or `brew uninstall`.

## Simple Usage

* If you don't have Brewfile

Initialize your Brewfile by:

    $ brew file init

You can see your Brewfile by:

    $ cat /usr/local/Library/Brewfile

* If you already have Brewfile

Copy your Brewfile to /usr/local/Library/Brewfile, and do:

    $ brew file install

## Use GitHub (or any git repository) for Brewfile management

Set a git repository by:

    $ brew file set_repo

    Set repository, "non" for local Brewfile.
    <user>/<repo> for GitHub repository,
    or full path for the repository: 

Then give a name like `rcmdnk/Brewfile`, or `git@github.com:rcmdnk/Brewfile`.

* If the repository doesn't exist

It enters a repository creation process (only for GitHub case).

To create a repository,
you need [Requests](http://docs.python-requests.org/en/latest/) module.

To install **Requests**, do:

    $ easy_install pip # in case you've not installed pip
    $ pip install requests

Once you created the repository,
do the first initialization by:

    $ brew file init

* If the repository exists

If the repository already have Brewfile, then do:

    $ brew file install

Otherwise initialize it:

    $ brew file init


## More details

[README.DETAILS.md](README.DETAILS.md)
