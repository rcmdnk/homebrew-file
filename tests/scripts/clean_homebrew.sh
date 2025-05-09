#!/usr/bin/env bash

brew list | xargs brew uninstall --zap --force
brew list --cask | xargs brew uninstall --cask --zap --force
brew tap | xargs brew untap

rm -rf "$(brew --cache)"
