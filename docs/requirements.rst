Requirements
============

- `Homebrew <https://github.com/mxcl/homebrew>`_ (Can be installed by the install script of brew-file, too).
- Python 2.7.7 or later, or Python 3.
- Requests module (optional)

Current macOS High Sierra's python (``/usr/bin/python``) is 2.7.10,
so that there is no need to do on python.

It calls ``/usr/bin/env python``, i.e., ``python`` command in your ``PATH``.

If you set your ``PYTHONPATH`` for python3
and ``python`` command is linked to python2,
you may need to execute ``brew-file`` directly::

    $ python3 /usr/local/bin/brew-file

instead of ``brew file``.

* `Can’t ignore unknown argument in subparser of ArgumentParser of Python even if parse_known_args is given <http://rcmdnk.github.io//en/blog/2015/03/08/computer-python/>`_

* `PythonのArgumentParserでsubparserを使うとparse_known_argsでもunknownな引数が無視できないエラーについて <http://rcmdnk.github.io/blog/2014/12/25/computer-python/>`_

Requests module of python is needed to create Brewfile repository with ``setup_repo``.
If you make the repository by yourself, it is not needed.

To install::

    $ easy_install pip # # in case you've not installed pip
    $ pip install requests
