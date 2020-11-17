brew-wrap
=========

If you want to automatically update Brewfile after ``brew install/uninstall``,
or ``mas install/uninstall``
please use ``brew-wrap``.

`homebrew-file/etc/brew-wrap <https://github.com/rcmdnk/homebrew-file/blob/master/etc/brew-wrap>`_
has a wrapper function ``brew``/``mas``.

Features:

* It executes ``brew file init`` after such ``brew install`` automatically.
* ``file`` can be skipped for non-conflicted commands with ``brew``.

  * e.g.) ``init`` command is not in ``brew``. Then, you can replace ``brew file init`` with::

      $ brew init

  * Such ``edit`` command is also in ``brew``. In this case, ``brew edit``
    executes original ``brew edit``.

    * But you can use ``brew -e`` or ``brew --edit`` to edit **Brewfile**.

To enable it, just read this file in your ``.bashrc`` or any of your setup file:

.. code-block:: sh

   if [ -f $(brew --prefix)/etc/brew-wrap ];then
     source $(brew --prefix)/etc/brew-wrap
   fi

``brew``/``mas`` function in ``brew-wrap`` executes original ``brew``/``mas``
if ``brew-file`` is not included.

Therefore, you can safely uninstall/re-install brew-file
even if you have already sourced it.

Some subcommands of ``brew-file`` can be used
as a subcommand of ``brew``, if the command is not in original brew subcommands.

Such ``init`` or ``casklist`` commands can be used like::

    $ brew init # = brew file init

    $ brew casklist # brew file casklist

With completion settings below,
``file`` is included in the completion list of ``brew``.

In addition, the completion for ``brew file`` is also enabled,
as same as ``brew-file`` command.

.. warning::

   Previously, ``brew-wrap`` was in ``bin/brew-wrap``,
   and it was used like ``alias brew="brew-wrap"``.

   If you have this obsolete setting, please delete and renew as above.

