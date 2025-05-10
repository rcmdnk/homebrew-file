#!/usr/bin/env bash

brew list --formula | xargs brew uninstall --formula --force
brew list --cask | xargs brew uninstall --cask --zap --force
brew tap | xargs brew untap
