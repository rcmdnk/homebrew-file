Development
===========

Preparation
-----------

To develop this package, use poetry::

    $ pip install poetry
    $ poetry install
    $ poetry shell

Then, you can run ``brew-file`` command made from ``src`` directory.

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

When you run ``git commit``, ``pre-commit`` will run ``black`` and other linters.

Some of parts will be automatically fixed
and you need just rerun ``git commit``.

Some of parts will be remained and you need to fix them manually.

Fix them and rerun ``git commit``.
