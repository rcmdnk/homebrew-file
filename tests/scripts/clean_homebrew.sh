#!/usr/bin/env bash

brew list | xargs brew uninstall --force
brew list --cask | xargs brew uninstall --cask --force
brew tap | xargs brew untap

rm -rf "$(brew --cache)"
rm -rf "$(brew --prefix)/Caskroom/*"
rm -rf ~/Library/Caches/Homebrew
rm -rf ~/Library/Logs/Homebrew
rm -rf ~/Library/Preferences/Homebrew
