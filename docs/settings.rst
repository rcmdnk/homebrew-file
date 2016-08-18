Settings
========

Following environmental variables can be used.

.. csv-table::
   :delim: |
   :header: Name, Description, Default

   HOMEBREW_BREWFILE              | Set place of Brewfile. | \"~/brewfile/Brewfile\"
   HOMEBREW_BREWFILE_BACKUP       | If it is set to not empty, Brewfile's back up is made to HOMEBREW_BREWFILE_BACKUP when Brewfile is updated. | \"\"
   HOMEBREW_BREWFILE_LEAVES       | Set 1 if you want to list up only leaves (formulae which don't have any dependencies, taken by `brew leaves`). | 0
   HOMEBREW_BREWFILE_TOP_PACKAGES | Packages which are listed in Brewfile even if `leaves` is used and they are under dependencies. (Useful for such `go`, which is used by itself, but some packages depend on it, too.) | \"\"
   HOMEBREW_BREWFILE_VERBOSE      | Set verbose level. | 1
   HOMEBREW_BREWFILE_APPSTORE     | Set 0 you don't want to list up AppStore applications Brewfile. | 1
   HOMEBREW_CASK_OPTS             | This is `Cask's option <https://github.com/caskroom/homebrew-cask/blob/master/USAGE.md>`_ to set cask environment. If caskroom or appdir is set with these options, Brew-file uses these values in it. | \"\"
