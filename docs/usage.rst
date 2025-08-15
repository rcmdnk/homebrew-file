Usage
=====

Brewfile
--------

Brew-file manages packages installed by Homebrew.
It also supports `brew-cask <https://github.com/phinze/homebrew-cask>`_
and other Homebrew subcommand installers.

It uses input file. By default, the file is **$XDG_CONFIG_HOME/brewfile/Brewfile**.
If you don't have ``$XDG_CONFIG_HOME`` environment variable, it is **~/.config/brewfile/Brewfile**.
You can reuse **Brewfile** for Brewdler, too.

If you want to specify input file, use ``-f`` option.

If you want to change default **Brewfile**, set environmental variable: ``HOMEBREW_BREWFILE``
in your setup file (e.g. **.bashrc**), like:

.. code-block:: sh

   export HOMEBREW_BREWFILE=~/.brewfile

You can also modify the default installation locations of Cask packages.
To make this settings, it is the same as issuing `How to Use Homebrew-cask#Options <https://github.com/homebrew/homebrew-cask/blob/master/USAGE.md#options>`_.
You might want to add the following line to your **.bashrc** or **.zshenv**:

.. code-block:: sh

    export HOMEBREW_CASK_OPTS="--appdir=$HOME/MyApplications"

If there is no **Brewfile**, Brew-file will ask you if you want to initialize **Brewfile**
with installed packages or not.
You can also make it with ``install`` (``-i``) subcommand.

With ``install`` subcommand, Brew-file tries to install packages listed in **Brewfile**.

**Brewfile** convention is similar as Brewdler.
Normally, you don't need to modify anything on Brewdler's **Brewfile** for Brew-file

Example::

    # Tap repositories and their packages
    tap rcmdnk/file
    brew brew-file

    # This will install all packages in rcmdnkpac
    tapall rcmdnk/rcmdnkpac

    # Homebrew packages
    brew mercurial
    brew macvim --with-lua

    # Cask packages
    tap homebrew/cask
    cask bettertouchtool

    # Additional files
    file ~/.Brewfile

First column is command.
Second to the last columns are package name and options.
They are used as arguments for such ``brew install``,
therefore any options of Homebrew can be used.

===============  ================================
Command          For what? (X is package+options)
===============  ================================
brew             ``brew install X``
install          Same as ``brew``
tap              ``brew tap X``
tapall           ``brew tap X``, and installs all packages of Formulae in the tap.
cask             ``brew install --cask X``.
cask_args        Arguments for cask command. e.g. ``cask_args appdir: "~/Applications", require_sha: true`` for ``brewdler``, ``bundle`` case, ``cask_args --appdir=~/Applications --require_sha``.
appstore         Apps installed from AppStore. The line is like: `appstore <identifier> <App Name>`. Identifier can be obtained by `argon/mas <https://github.com/argon/mas>`_. (It will be installed automatically.) For older OS X, it might be not available. For such a case, only App names are listed by ``init``, and ``install`` command just warns like ``Please install <App Name> from App Store!``.
whalebrew        Images managed by `Whalebrew <https://github.com/whalebrew/whalebrew>`_.
vscode           `Visual Studio Code extensions <https://marketplace.visualstudio.com/vscode>`_.
cursor           `Cursor extensions <https://www.cursor.com/>`_.
codium           `VSCodium extensions <https://vscodium.com/>`_.
main             Main file. If it exists, new packages will be written to the main file instead of the top file.
file             Additional files. A path is a absolute path, or a relative path, relative to the file which calls it. You can use environmental variables such ``file ~/${HOSTNAME}.Brewfile``.
brewfile         Same as ``file``.
before           Execute ``X`` at the beginning of the install.
after            Execute ``X`` after all install commands.
Anything others  Execute the line (first and other columns as one line) before ``after`` is executed.
===============  ================================

If the second column is ``install``, it will be ignored.

i.e. ``brew install package`` is same as ``brew package``.

If you want to build macvim with lua option, you can write as above example **Brewfile**.

If you use ``tap``, Brew-file only does ``tap`` the repository.

If you use ``tapall``, Brew-file does ``brew install`` for all Formulae in the repository
in addition to do ``tap`` the repository.

If you want to divide the list into several files.
If the top **Brewfile** has ``main``, ``file`` or ``brewfile`` commands,
then corresponding argument is used as an external file.
The path can be an absolute or a relative.
If you use a relative path, like **./Brewfile2**,
then the start directory is the directory
where the main **Brewfile** is.

You can use a nest of ``file``, too.
The relative path starts from the parent file's directory.

You can also use nested ``main``,
though it should be no more than once in one Brewfile.

For the path, such ``~`` is translated into ``$HOME``.
You can use some shell variables: ``$HOSTNAME``, ``$HOSTTYPE`` and ``$OSTYPE``.
Inaddition, ``$PLATFORM``, which is platform identifier like
darwin, linux, or win32.

If you use `brew-wrap <https://homebrew-file.readthedocs.io/en/latest/brew-wrap.html>`_,
any environmental variables can be used.

.. warning::

    Environmental variables are not translated if you do not use brew-wrap or
    call brew directly like ``command brew``.
    Only ``~``, ``$HOME``, ``$HOSTNAME``, ``$HOSTTYPE``, ``$OSTYPE``, and ``$PLATFORM``
    are translated in these cases.

e.g.

If you have::

    file ./${HOSTNAME}.Brewfile

in main ``Brewfile``, and prepare files like::

    Brewfile Host1.Brewfile Host2.Brewfile Host3.Brewfile

in the same directory,
then ``brew-file`` picks up **Host1.Brewfile** for Host1,
and **Host2.Brewfile** for Host2, etc...

Or if you just have::

    file ~/.Brewfile

then you can put Host specific packages in **~/.Brewfile**.
(If the file doesn't exist, ``brew-file`` just ignores it.)

Other example: `Add an option to ignore appstore apps · Issue #22 · rcmdnk/homebrew-file <https://github.com/rcmdnk/homebrew-file/issues/22>`_

Some packages such macvim has Application (MacVim.app).
If you want to install them to Applications area,
please use ``-l`` (for ``~/Applications/``) or ``-g`` (for ``/Applications/``).

You can run update/install/clean/clean_non_request/pull/push as dry run mode with option `-d`/`--dry_run`.

If you want edit **Brewfile**, use ``edit`` option.

.. warning::

   If you do ``brew file edit`` before installing ``Brewfile`` and save w/o any modification,
   you may make empty ``Brewfile`` (Be careful, ``brew -c -C`` remove all packages :scream:).
   Therefore I recommend you to do ``brew file -i`` at first if you don't have ``Brewfile``.


Manage Brewfile with Git
------------------------

You can maintain your **Brewfile** at the git repository.
First, make new repository at GitHub (or other git server),
which has a file named **Brewfile**.

Then, set the repository by::

    $ brew file set_repo -r <repository>

It will clone the repository.
The content of **Brewfile** in the repository will be used instead of
**$XDG_CONFIG_HOME/brewfile/Brewfile**.
(then **$XDG_CONFIG_HOME/brewfile/Brewfile** will have this repository information.)

``repository`` should be like `rcmdnk/Brewfile <https://github.com/rcmdnk/Brewfile>`_ in GitHub,
which should have **Brewfile** (different file name can be used by ``-f``).

If you want to use other hosts than github, use full path for the repository, like::

    $ brew file set_repo -r git@bitbucket.org:rcmdnk/my_brewfile

If the repository doesn't have **Brewfile** (or specified by ``-f``, ``brew file init`` initialize the file.
Then, you can push it by ``brew file push``.

With this procedure, you can synchronize all your Mac easily :thumbsup:

To install new package, use::

    $ brew file brew install <package>

instead of ``brew install <package>``, because above command
automatically update **Brewfile**.

This is useful especially if you are using the repository for the **Brewfile**,
and want to use ``brew file update``.

Otherwise, please be careful to use ``brew file update``,
because it deletes what you installed, but you have not registered in **Brewfile**.


Check Apps
----------

If you want to check your Apps for Cask, use::

    $ brew file casklist

This command makes ``Caskfile.txt``, which is like::

    ### Cask applications
    ### Please copy these lines to your Brewfile and use with `brew bundle`.

    ### tap and install Cask (remove comment if necessary).
    #tap homebrew/cask
    #install brew-cask

    ### Apps installed by Cask in /Applications
    cask install adobe-reader # /Applications/Adobe Reader.app
    cask install xtrafinder # /Applications/XtraFinder.app

    ### Apps installed by Cask in /Applications/Utilities:
    cask install xquartz # /Applications/Utilities/XQuartz.app

    ### Apps installed by Cask in ~/Applications.
    cask install bettertouchtool.rb # ~/Applications/BetterTouchTool.app

    #############################

    ### Apps not installed by Cask, but installed in /Applications.
    ### If you want to install them with Cask, remove comments.
    #cask install keyremap4macbook # /Applications/KeyRemap4MacBook.app

    ### Apps not installed by Cask, but installed in /Applications/Utilities:
    ### If you want to install them with Cask, remove comments.

    ### Apps not installed by Cask, but installed in ~/Applications.
    ### If you want to install them with Cask, remove comments.
    #cask install copy.rb # ~/Applications/Copy.app


    #############################

    ### Apps not registered in Cask, but installed in /Applications.
    # /Applications/App Store.app
    # /Applications/Calendar.app
    ...

    ### Apps not registered in Cask, but installed in /Applications/Utilities:
    ...

    ### Apps not registered in Cask, but installed in ~/Applications.

You can find applications which were installed manually,
but can be managed by Cask under "Apps not installed by Cask, but installed in...".

If you want to manage them with **Brewfile**, just copy above lines w/o "#" for these Apps.

Use machine specific Brewfile
-----------------------------

You can share Brewfile at different machines
by using Dropbox or Git repository `Getting Started <https://homebrew-file.readthedocs.io/en/latest/getting_started.html>`_.

You may also want to have each machine specific packages.

In this case, ``main`` command is useful.

First, make Brewfile with common packages:

.. code-block:: sh

    tap homebrew/core
    brew bash
    brew neovim

    main ./Brewfile.$HOSTNAME

and share it for each machine.

Then, install packages at the machine A.

If you set `brew-wrap <https://homebrew-file.readthedocs.io/en/latest/brew-wrap.html>`_
or run ``brew file init``,
new packages will be written into **Brewfile.A**
in the same directory as **Brewfile**.

If you install packages at the machine B,
then new packages will be written into **Brewfile.B**.

If you have new packages which are common in **Brewfile.A** and **Brewfile.B**,
edit these files and move the packages into **Brewfile**.

If you want to have package lists for each platform,
it may useful to have ``main`` command like::

    main ./Brewfile.$OSTYPE.$PLATFORM

This will make unique names like:

* macOS, M1 (arm environment): **Brewfile.darwin.arm64**
* macOS, Intel or x86_64 environment at M1: **Brewfile.darwin.x86_64**
* Linux, 64 bit: **Brewfile.linux.x86_64**
* Cygwin, 64 bit: **Brewfile.cygwin.x86_64**

Share Brewfile with your colleagues
-----------------------------------

If you are working with in a group, it is good to have a common Brewfile
to share the development environment.

In this case, make **Brewfile** like:

.. code-block:: sh

    tap homebrew/core
    brew bash
    brew neovim
    ...

    main ~/.config/MyBrewfile

Then, maintain **Brewfile** for the group.
It is useful to share it by GitHub.
Each developer can update the environment by ``brew file update``.

In addition, each developer can install his/her necessary packages
and maintain them by *MyBrewfile**.
