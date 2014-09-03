#!/bin/sh
set -e
f (){
  echo \$ $*
  $*
}
f export PAGER=cat
f export EDITOR=cat
f export VISUAL=cat
f brew install rcmdnk/file/brew-file $version
f brew file version
f brew file help
f brew install vim --with-lua --HEAD
f brew install caskroom/cask/brew-cask
f brew cask install firefox
touch "$(brew --prefix)/Library/Brewfile"
f brew file init -y
f brew file update -y
f brew file casklist
f brew file edit
