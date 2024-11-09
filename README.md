# Brew-file

[![Test](https://github.com/rcmdnk/homebrew-file/actions/workflows/test.yml/badge.svg)](https://github.com/rcmdnk/homebrew-file/actions/workflows/test.yml)
[![Coverage Status](https://img.shields.io/badge/Coverage-check%20here-blue.svg)](https://github.com/rcmdnk/homebrew-file/tree/coverage)
[![Documentation Status](https://readthedocs.org/projects/homebrew-file/badge/?version=latest)](http://homebrew-file.readthedocs.io/en/latest/?badge=latest)

A powerful Brewfile manager for [Homebrew](http://brew.sh/) on macOS and Linux.

## Installation

Install Brew-file via Homebrew:

```sh
brew install rcmdnk/rcmdnkpac/homebrew-file
```

Once installed, you can use the `brew file` command.

## Features

Brew-file enhances your Homebrew experience with the following features:

- **Brewfile-Based Package Management**

  - Use `brew file init` to generate a Brewfile from currently installed packages.
  - Use `brew file install` to install packages listed in a Brewfile.

- **Supports Various Package Types**

  - Homebrew formulae, casks and taps.
  - Apps installed from the Mac App Store.
  - [whalebrew](https://github.com/whalebrew/whalebrew) images.
  - Extensions for [Visual Studio Code](https://marketplace.visualstudio.com/vscode).

- **Automatic Brewfile Updates**

  - Set up [brew-wrap](https://homebrew-file.readthedocs.io/en/latest/brew-wrap.html) to automatically update your Brewfile on `brew install`, `brew uninstall`, and other package changes.

- **Brewfile Shareing, Version Control**

  - Easily share and manage your Brewfile using [Git integration](https://homebrew-file.readthedocs.io/en/latest/usage.html#manage-brewfile-with-git).
  - `brew file update` will pull the latest changes from the remote repository, install/uninstall based on the changes, update Brewfile, commit and push the changes.

- **Flexible Brewfile Organization**

  - Organize packages by environment with customized Brewfiles, like:
    - `Brewfile` for common packages across systems.
    - `Brewfile.linux` for Linux-specific packages.
    - `Brewfile.mac` for macOS-specific packages.
    - `Brewfile.$HOSTNAME` for host-specific packages.

For more information, see the [Brew-file Documentation](http://homebrew-file.readthedocs.io/en/latest/).
