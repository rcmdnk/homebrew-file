Usage
=====

Following environmental variables can be used.

===========================      ================================
Name                             Description
===========================      ================================
HOMEBREW_BREWFILE                Set place of Brewfile (Default: ~/brwefile/Brewfile).
HOMEBREW_BREWFILE_BACKUP         If it is set to not empty, Brewfile's back up is made to HOMEBREW_BREWFILE_BACKUP when Brewfile is updated. (Default: "")
HOMEBREW_FILE_VERBOSE            Set verbose level. (Default: 1)
HOMEBREW_FILE_APPSTORE           Set if AppStore applications is listed in Brewfile or not. (Default: True)
HOMEBREW_CASK_OPTS               This is [Cask's option](https://github.com/caskroom/homebrew-cask/blob/master/USAGE.md) to set cask environment.
                                 If caskroom or appdir is set with these options, Brew-file uses these values in it.
===========================      ================================
