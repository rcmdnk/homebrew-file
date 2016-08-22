Brew-file
=========

[![Build Status](https://travis-ci.org/rcmdnk/homebrew-file.svg?branch=master)](https://travis-ci.org/rcmdnk/homebrew-file)
[![Coverage Status](https://coveralls.io/repos/rcmdnk/homebrew-file/badge.png?branch=master)](https://coveralls.io/r/rcmdnk/homebrew-file?branch=master)
[![Documentation Status](https://readthedocs.org/projects/homebrew-file/badge/?version=latest)](http://homebrew-file.readthedocs.io/en/latest/?badge=latest)

Brewfile manager for Homebrew, inspired by [Brewdler](https://github.com/andrew/brewdler)
(Brew-file was Renamed from brewall).

Brewfile dumped by [homebrew-brewdler](https://github.com/Homebrew/homebrew-brewdler)
can be used as input, too.

## Note

17/Dec/2015 update:

The default place of Brewfile has been changed from:

    /usr/local/Library/Brewfile

to

    ~/.brewfile/Brewfile

because Homebrew deletes files under **/usr/local** other than
Homebrew's one when such `brew update` is executed.
(Homebrew checkout its repository as **/usr/local**.)

If you used default settings, you may lose Brewfile.

In such case, please try `brew file init` and chose local Brewfile, which makes
new file **~/.brewfile/Brewfile**.

If you used git repository, you might see a output when you executed `brew update`:

    $ brew update
    Ignoring path Library/rcmdnk_Brewfile/
    To restore the stashed changes to /usr/local run:
      `cd /usr/local && git stash pop`
      Already up-to-date.

In this case, please delete **/usr/local/Library/<your_git_account>_Brewfile**,
then do `brew file init` and set repository.

New repository will be checked out to **~/.brewfile/<your_git_account>_Brewfile**.

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

**brew-wrap** wraps the original `brew` command
for an automatic update of **Brewfile** when you execute
such a `brew install` or `brew uninstall`.

## Use local Brewfile

By default, **Brewfile** is **~/.brewfile/Brewfile**.

If you don't have **Brewfile**, first, do:

    $ brew init

`brew init` is same as `brew file init`, if you setup `brew-wrap` as above.

Note: In below, `set_repo` command can be used directly after `brew`,
but `install` or `update` need to use with `brew file` because
`brew` command has own `install` or `update` commands.

You can check your package list by:

    $ brew file cat

If you already have **Brewfile**, then copy it to 
**~/.brewfile/Brewfile**
and install packages listed in **Brewfile** by:

    $ brew file install

After that, you need to do only normal `brew` commands, like `brew install` or `brew uninstall`.
After each command, **Brewfile** is updated automatically
if you set `brew-wrap` as above.

When you get new Mac, copy 
**~/.brewfile** to new Mac
and just do:

    $ brew file install

## use Dropbox (or any online storages) for Brewfile management

### Set Brewfile place

You can set the place of Brewfile by using the environment variable like:

    export HOMEBREW_BREWFILE=~/Dropbox/Brewfile

Then, you can use Brewfile as same as the original Brewfile place.

In this case, when you have new Mac,
set `HOMEBREW_BREWFILE` and synchronize the file with a online storage service,
then do:

    $ brew file install

If you are using multiple Mac in the same time,
it is good to have a cron job like

    30 12 * * * brew file update

This command installs new packages which were installed in another Mac
at a lunch time (12:30) every day.

This command also does `brew update && brew upgrade`,
and removes packages not listed in `Brewfile`.

If you want to do only installing new packages, then set as:

    30 12 * * * brew file install

## Use GitHub (or any git repository) for Brewfile management

### Set up a repository

First, create a repository with a file named **Brewfile**.

If you use GitHub, you can make it with brew-file:

    $ brew set_repo

    Set repository, "non" for local Brewfile.
    <user>/<repo> for GitHub repository,
    or full path for the repository: 

Give a name like `rcmdnk/Brewfile` (will be recognized as a GitHub repository),
or such `git@github.com:rcmdnk/Brewfile`.

Then, initialize **Brewfile**:

    $ brew init

### Set up new Mac with your Brewfile in the repository

Do:

    $ brew set_repo

and give your repository name.

And install packages listed in **Brewfile** like:

    $ brew file install

### Brewfile management

To update the repository, do:

    $ brew file update

If you have set the repository,
this command does `git pull` and `git push`
in addition to such brew's `install`, `clean`, `update`, `updgrade` and removing packages
described in online storages section above.

It is good if you have such a cron job like:

    30 12 * * * brew file update

The repository is updated at lunch time every day.

## More details

[README.MORE.md](README.MORE.md)
