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


Commit
------

When you run ``git commit``, ``pre-commit`` will run ``ruff`` and other linters/formatters.

Some of parts will be automatically fixed
and you need just rerun ``git commit``.

Some of parts will be remained and you need to fix them manually.

Fix them and rerun ``git commit``.

`pre-push` will be run before push, which will confirm if `combine.sh` is run or not and version information is updated or not.
