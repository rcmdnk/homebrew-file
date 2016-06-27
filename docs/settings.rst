Settings
========

Following environmental variables can be used.

==============================      ================================
Name                                Description
==============================      ================================
HOMEBREW_BREWFILE                   Set place of Brewfile (Default: ~/brwefile/Brewfile).
HOMEBREW_BREWFILE_BACKUP            If it is set to not empty, Brewfile's back up is made to HOMEBREW_BREWFILE_BACKUP when Brewfile is updated. (Default: "")
HOMEBREW_BREWFILE_LEAVES            Set 1 if you want to list up only leaves (formulae which don't have any dependencies, taken by `brew leaves`).
HOMEBREW_BREWFILE_TOP_PACKAGES      Packages which are listed in Brewfile even if `leaves` is used and they are under dependencies. (Useful for such `go`, which is used by itself, but some packages depend on it, too.)
HOMEBREW_FILE_VERBOSE               Set verbose level. (Default: 1)
HOMEBREW_FILE_APPSTORE              Set if AppStore applications is listed in Brewfile or not. (Default: True)
HOMEBREW_CASK_OPTS                  This is `Cask's option <https://github.com/caskroom/homebrew-cask/blob/master/USAGE.md>`_ to set cask environment.
                                    If caskroom or appdir is set with these options, Brew-file uses these values in it.
==============================      ================================
