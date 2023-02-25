Settings
========

Following environmental variables can be used.

.. csv-table::
   :delim: |
   :header: Name, Description, Default

   HOMEBREW_BREWFILE              | Set place of Brewfile. | \"~/brewfile/Brewfile\"
   HOMEBREW_BREWFILE_BACKUP       | If it is set to not empty, Brewfile's back up is made to HOMEBREW_BREWFILE_BACKUP when Brewfile is updated. | \"\"
   HOMEBREW_BREWFILE_LEAVES       | Set 1 if you want to list up only leaves (formulae which don't have any dependencies, taken by `brew leaves`). | 0
   HOMEBREW_BREWFILE_ON_REQUEST   | Set 1 if you want to list up only packages installed on request. If it is set 1, it is given priority over `LEAVES` option. Note: This list can be changed if packages installed by brew-file in new machine. (some "on_request" package could be installed as "as_dependencies" of others before being installed on request.)| 0
   HOMEBREW_BREWFILE_TOP_PACKAGES | Packages which are listed in Brewfile even if `leaves` is used and they are under dependencies. (Useful for such `go`, which is used by itself, but some packages depend on it, too.) | \"\"
   HOMEBREW_BREWFILE_FETCH_HEAD   | Set 1 if you want to use `--fetch-HEAD` for `brew upgrade` option at `brew file update`.
   HOMEBREW_BREWFILE_EDITOR       | Set editor to be used by `brew file edit`. If you use `brew-wrap` or call `brew-file` directly, the environmental variable `EDITOR` also works. If you do not use `brew-file` and do not set this variable, `EDITOR` does not work and the system default editor will be used.| \"\"
   HOMEBREW_BREWFILE_VERBOSE      | Set verbose level ("debug", "info", "warning", "error", "critical"). | "info"
   HOMEBREW_BREWFILE_APPSTORE     | Set Appstore application management level. 0: do not, 1: manage fully, 2: use list to install, but do not update by init command even if new App is added (but package is removed from the list at ``brew file brew mas uninstall <app id>``).| 1
   HOMEBREW_CASK_OPTS             | This is `Cask's option <https://github.com/homebrew/homebrew-cask/blob/master/USAGE.md>`_ to set cask environment. If appdir or fontdir is set with these options, Brew-file uses these values in it. | \"\"
