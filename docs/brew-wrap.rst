brew-wrap
=========

If you want to automatically update Brewfile after ``brew install/uninstall``,
``mas install/uninstall``, ``whalebrew install/uninstall`` and ``code --install-extension/uninstall-extension``,
please use ``brew-wrap``.

`homebrew-file/etc/brew-wrap <https://github.com/rcmdnk/homebrew-file/blob/main/etc/brew-wrap>`_
has a wrapper function for these commands.

Feature summary
---------------

* It executes ``brew file init`` after such ``brew install`` automatically.
* ``file`` can be skipped for non-conflicted commands with ``brew``.

  * e.g.) ``init`` command is not in ``brew``. Then, you can replace ``brew file init`` with::

      $ brew init

  * Such ``edit`` command is also in ``brew``. In this case, ``brew edit``
    executes original ``brew edit``.

    * But you can use ``brew -e`` or ``brew --edit`` to edit **Brewfile**.
* Users can add actions after Brewfile update by using `_post_brewfile_update`.

How to enable it
----------------

To enable it, just read this file in your **.bashrc** or **.zshrc**:

.. code-block:: sh

    if [ -f $(brew --prefix)/etc/brew-wrap ];then
      source $(brew --prefix)/etc/brew-wrap
    fi

Or, for Fish Shell add the following lines in your **config.fish** to wrap ``brew`` command:

.. code-block:: sh

    if test -f (brew --prefix)/etc/brew-wrap.fish
      source (brew --prefix)/etc/brew-wrap.fish
    end

Command wrapper functions in ``brew-wrap`` executes original commands
if ``brew-file`` is not included.

Therefore, you can safely uninstall/re-install brew-file
even if you have already sourced it.

.. warning::

   Previously, ``brew-wrap`` was in ``bin/brew-wrap``,
   and it was used like ``alias brew="brew-wrap"``.

   If you have this obsolete setting, please delete and renew as above.


Direct call of brew-file subcommands
------------------------------------

Some subcommands of ``brew-file`` can be used
as a subcommand of ``brew``, if the command is not in original brew subcommands.

Such ``init`` or ``casklist`` commands can be used like::

    $ brew init # = brew file init

    $ brew casklist # brew file casklist

With completion settings below,
``file`` is included in the completion list of ``brew``.

In addition, the completion for ``brew file`` is also enabled,
as same as ``brew-file`` command.

_post_brewfile_update
----------------------

You can add actions after anytime Brewfile updated.

To add actions, define `_post_brewfile_update` function in your **.bashrc** or **.zshrc**, after `brew-wrap`, like:

.. code-block:: sh

    if [ -f $(brew --prefix)/etc/brew-wrap ];then
      source $(brew --prefix)/etc/brew-wrap

      _post_brewfile_update () {
        echo "Brewfile was updated!"
      }
   fi
