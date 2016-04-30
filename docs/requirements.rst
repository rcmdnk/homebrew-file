Requirements
============

- `Homebrew <https://github.com/mxcl/homebrew>`_ (Can be installed by the install script of brew-file, too).
- Python 2.7.7 or later (optional).
- Requests module (optional)

Although it is not mandatory,
the latest Python 2.7.x or 3.x is recommended,
to use ``brew file brew`` command (and ``brew-wrap``).

You can install the latest python2.x by Homebrew::

    $ brew install python

or python3.x::

    $ brew install python3


If you set your ``PYTHONPATH`` for python3,
you may need to execute brew-file directly::

    $ python3 /usr/local/bin/brew-file

instead of ``brew file``.

* `Can’t ignore unknown argument in subparser of ArgumentParser of Python even if parse_known_args is given <http://rcmdnk.github.io//en/blog/2015/03/08/computer-python/>`_

* `PythonのArgumentParserでsubparserを使うとparse_known_argsでもunknownな引数が無視できないエラーについて <http://rcmdnk.github.io/blog/2014/12/25/computer-python/>`_

Requests module of python is needed to create Brewfile repository with ``setup_repo``.
If you make the repository by yourself, it is not needed.

To install::

    $ easy_install pip # # in case you've not installed pip
    $ pip install requests
