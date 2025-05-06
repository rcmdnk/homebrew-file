Development
===========

Preparation
-----------

To develop this package, use `uv <https://docs.astral.sh/uv/>`_::

    $ uv sync
    $ source .venv/bin/activate

Then, you can run ``brew-file`` command made from ``src`` directory.

Now you can also use `pre-commit` command.

Install `pre-commit` settings by::

    $ pre-commit install --hook-type pre-commit --hook-type pre-push


Update scripts
--------------

Do not edit ``bin/brew-file`` directly.

Edit ``src/brew_file/*.py`` and run::

    $ ./combine.sh


Test
----

Run::

    $ pytest


Tests in ``tests`` will test ``bin/brew-file`` instead of files in ``src``, therefore run ``combine.sh`` before run tests.


Test real Homebrew environment with lume
----------------------------------------

Most of `pytest` runs tests in the mocked environment
in which installing/uninstalling Homebrew packages is not actually done.

Tests in ``tests/test_serial.py`` (``marker: serial``) will run in the real Homebrew environment
but they are not included in the default test run
as they change the Homebrew environment.

To run these tests, you can use lume to create a macOS VM.

Prepare VM with lume
^^^^^^^^^^^^^^^^^^^^

Install lume::

    $ brew install trycua/lume/lume

Pull VM with xcode::

    $ lume pull macos-sequoia-xcode:latest

Ref: `cua/libs/lume/README.md <https://github.com/trycua/cua/blob/main/libs/lume/README.md>`_

Prepare cert if needed (in zero trust or etc...)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Example for Zero trust (`Install certificate manually · Cloudflare Zero Trust docs <https://developers.cloudflare.com/cloudflare-one/connections/connect-devices/user-side-certificates/manual-deployment/>`_).

Launch the VM with shared directory to access the installed cert::

    $ lume run macos-sequoia-xcode:latest --shared-dir "/Library/Application Support/Cloudflare:ro"

Login with username: 'lume', password: 'lume'.

Open terminal and prepare cert::

    lume@lumes-Virtual-Machine ~ % cp /Volumes/My\ Shared\ Files/installed_cert.pem ./Documents/
    lume@lumes-Virtual-Machine ~ % sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain ./Documents/installed_cert.pem

From other terminal, stop VM::

    $ lume stop macos-sequoia-xcode:latest

Prepare Homebrew, python libraries, etc...
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Launch vm w/o display::

    $ lume run macos-sequoia-xcode:latest --no-display

From other terminal, check ip of VM::

    $ lume ls
    name                              os      cpu     memory  disk            display     status          storage         ip              vnc
    macos-sequoia-xcode_latest        macOS   4       8.00G   22.5GB/50.0GB   1024x768    running         default         192.168.64.2    vnc://:clear-banana-blue-river@127.0.0.1:56109

Login to VM::

    $ ssh lume@192.168.64.2
    (lume@192.168.64.2) Password: # password is also 'lume'
    lume@lumes-Virtual-Machine ~ %

Prepare Homebrew::

    lume@lumes-Virtual-Machine ~ % /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" # sudo password is also 'lume'
    lume@lumes-Virtual-Machine ~ % echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> $HOME/.zprofile
    lume@lumes-Virtual-Machine ~ % brew ls
    ==> Formulae

    ==> Casks

Install pytest, filelock by pip::

    lume@lumes-Virtual-Machine ~ % pip3 install pytest filelock
    lume@lumes-Virtual-Machine ~ % echo 'PATH=$HOME/Library/Python/3.9/bin:$PATH' >> $HOME/.zprofile

Make a link to the shared directory::

    lume@lumes-Virtual-Machine ~ % ln -s /Volumes/My\ Shared\ Files $HOME/shared

Exit and stop VM::

    lume@lumes-Virtual-Machine ~ % exit
    $ lume stop macos-sequoia-xcode:latest


Run test in VM
^^^^^^^^^^^^^^

Launch the VM with shared directory to access the repo::

    $ cd <path to repo>
    $ lume run macos-sequoia-xcode:latest --shared-dir "$PWD:ro"


From other terminal, login to VM::

Login to VM::

    $ ssh lume@192.168.64.2 # check ip of VM with 'lume ls'
    (lume@192.168.64.2) Password: # password is also 'lume'
    lume@lumes-Virtual-Machine ~ %

Run pytest::

    $ cd shared
    $ pytest -p no:cacheprovider -o "markers=serial" -c /dev/null tests/test_serial.py


Commit
------

When you run ``git commit``, ``pre-commit`` will run ``ruff`` and other linters/formatters.

Some of parts will be automatically fixed
and you need just rerun ``git commit``.

Some of parts will be remained and you need to fix them manually.

Fix them and rerun ``git commit``.

`pre-push` will be run before push, which will confirm if `combine.sh` is run or not and version information is updated or not.
