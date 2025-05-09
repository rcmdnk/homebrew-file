#!/usr/bin/env bash

brew list --formula | xargs brew uninstall --formula --zap --force
brew list --cask | xargs brew uninstall --cask --zap --force
brew tap | xargs brew untap

rm -rf "$(brew --cache)"
