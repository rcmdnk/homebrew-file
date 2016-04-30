Installation
============

Install Homebrew-file with Homebrew:

    $ brew install rcmdnk/file/brew-file

or you can use install script::

    $ curl -fsSL https://raw.github.com/rcmdnk/homebrew-file/install/install.sh |sh

Then, add following lines in you **.bashrc** or **.zshrc** to wrap *brew* command::

    if [ -f $(brew --prefix)/etc/brew-wrap ];then
      source $(brew --prefix)/etc/brew-wrap
    fi

**brew-wrap** wraps the original *brew* command
for an automatic update of **Brewfile** when you execute
such a `brew install` or `brew uninstall`.
