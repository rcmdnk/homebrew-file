Installation
============

Install Homebrew-file with Homebrew::

    $ brew install rcmdnk/file/brew-file

or you can use install script::

    $ curl -fsSL https://raw.github.com/rcmdnk/homebrew-file/install/install.sh |sh

which installs Homebrew itself, too, if it is not installed.

Then, add following lines in you **.bashrc** or **.zshrc** to wrap `brew` command::

    if [ -f $(brew --prefix)/etc/brew-wrap ];then
      source $(brew --prefix)/etc/brew-wrap
    fi

**brew-wrap** wraps the original `brew` command
for an automatic update of **Brewfile** when you execute
such a `brew install` or `brew uninstall`.

.. note::

  17/Dec/2015 update
  
  The default place of Brewfile has been changed from::
  
      /usr/local/Library/Brewfile
  
  to::
  
      ~/.brewfile/Brewfile
  
  because Homebrew deletes files under **/usr/local** other than
  Homebrew's one when such `brew update` is executed.
  (Homebrew checkout its repository as **/usr/local**.)
  
  If you used an old default setting (**/usr/local/Library/Brewfile**), you might lose Brewfile.
  
  In such case, please try `brew file init` and chose local Brewfile, which makes
  new file **~/.brewfile/Brewfile**.
  
  If you used git repository, you might see a output when you executed `brew update`::
  
      $ brew update
      Ignoring path Library/rcmdnk_Brewfile/
      To restore the stashed changes to /usr/local run:
        `cd /usr/local && git stash pop`
        Already up-to-date.
  
  In this case, please delete **/usr/local/Library/<your_git_account>_Brewfile**,
  then do `brew file set_repo`.
  
  New repository will be checked out to **~/.brewfile/<your_git_account>_Brewfile**.
