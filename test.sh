#!/bin/sh
brew install rcmdnk/file/brew-file $version
brew file version
brew file help
brew install vim --with-lua --HEAD
brew install caskroom/cask/brew-cask
brew cask install firefox
#brew file init
#brew file update
#brew file casklist
#brew file edit
