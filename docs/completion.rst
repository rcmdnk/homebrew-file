Completion
==========

Functions for Bash/Zsh completions are also installed.

For Bash, please install
`Bash-Completion <http://bash-completion.alioth.debian.org/>`_
by::

    $ brew install bash-completion

then, add following settings to your **.bashrc**:

.. code-block:: sh

   brew_completion=$(brew --prefix 2>/dev/null)/etc/bash_completion
   if [ $? -eq 0 ] && [ -f "$brew_completion" ];then
     source $brew_completion
   fi

For Zsh, add following settings in your **.zshrc**:

.. code-block:: sh

   brew_completion=$(brew --prefix 2>/dev/null)/share/zsh/zsh-site-functions
   if [ $? -eq 0 ] && [ -d "$brew_completion" ];then
     fpath=($brew_completion $fpath)
   fi
   autoload -U compinit
   compinit

In case you have installed `zsh-completions <https://github.com/zsh-users/zsh-completions>`_
 (can be installed by brew: ``$ brew install zsh-completions``), settings can be like:

.. code-block:: sh

   for d in "/share/zsh-completions" "/share/zsh/zsh-site-functions";do
     brew_completion=$(brew --prefix 2>/dev/null)$d
     if [ $? -eq 0 ] && [ -d "$brew_completion" ];then
       fpath=($brew_completion $fpath)
     fi
   done
   autoload -U compinit
   compinit

If you are using ``brew-wrap``, please write these completion settings
**BEFORE** ``brew-wrap`` reading.
