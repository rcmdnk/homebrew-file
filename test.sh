#!/bin/sh
f (){
  echo $*
  $*
}
f brew install rcmdnk/file/brew-file $version
f brew file version
f brew file help
f brew install vim --with-lua --HEAD
f brew install caskroom/cask/brew-cask
f brew cask install firefox
#brew file init
#brew file update
#brew file casklist
#brew file edit
