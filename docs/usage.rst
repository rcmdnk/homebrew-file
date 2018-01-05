Usage
=====

Brew-file manages packages installed by Homebrew.
It also supports `brew-cask <https://github.com/phinze/homebrew-cask>`_
and other Homebrew subcommand installers.

It uses input file. By default, the file is **~/.config/brewfile/Brewfile**.
You can reuse ``Brewfile`` for Brewdler, too.

If you want to specify input file, use ``-f`` option.

If you want to change default ``Brewfile``, set environmental variable: ``HOMEBREW_BREWFILE``
in your setup file (e.g. **.bashrc**), like:

.. code-block:: sh

   export HOMEBREW_BREWFILE=~/.brewfile

You can also modify the default installation locations of Cask packages.
To make this settings, it is the same as issuing `How to Use Homebrew-cask#Options <https://github.com/caskroom/homebrew-cask/blob/master/USAGE.md#options>`_.
You might want to add the following line to your **.bashrc** or **.zshenv**:

.. code-block:: sh

    export HOMEBREW_CASK_OPTS="--appdir=$HOME/MyApplications"

Similarly, you can specify the environment for brew-gem.  The following will tell brew-gem to use the Ruby installed by Homebrew itself:

.. code-block:: sh

    export HOMEBREW_GEM_OPTS="--homebrew-ruby"

If there is no ``Brewfile``, Brew-file will ask you if you want to initialize ``Brewfile``
with installed packages or not.
You can also make it with ``install`` (``-i``) subcommand.

With ``install`` subcommand, Brew-file tries to install packages listed in ``Brewfile``.
If any packages managed with Homebrew Cask are listed, brew-cask is also installed automatically.

``Brewfile`` convention is similar as Brewdler.
Normally, you don't need to modify anything on Brewdler's ``Brewfile`` for Brew-file

Example::

    # Tap repositories and their packages
    tap caskroom/cask
    brew 'brew-cask'
    # install brew-cask # install is same as "brew". Quotes are not mandatory.

    tapall rcmdnk/file # This will trigger `brew install brew-file`, too

    # Cask packages
    cask firefox
    #cask install firefox # "cask install" is same as "cask"

    # Other Homebrew packages
    brew mercurial
    brew macvim --with-lua

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
cask             ``brew cask install X``. Require `caskroom/homebrew-cask <https://github.com/caskroom/homebrew-cask/>`_. (It will be installed automatically.)
pip              `brew pip X`. Require `hanxue/brew-pip <https://github.com/hanxue/brew-pip>`_. (It will be installed automatically.)
gem              ``brew gem install X``. Require `sportngin/brew-gem <https://github.com/sportngin/brew-gem>`_. (It will be installed automatically.)
appstore         Apps installed from AppStore. The line is like: `appstore <identifier> <App Name>`. Identifier can be obtained by `argon/mas <https://github.com/argon/mas>`_. (It will be installed automatically.) For older OS X, it might be not available. For such a case, only App names are listed by ``init``, and ``install`` command just warns like ``Please install <App Name> from App Store!``.
file             Additional files. A path is a absolute path, or a relative path, relative to the file which calls it. You can use environmental variables such ``file ~/${HOSTNAME}.Brewfile``.
brewfile         Same as ``file``.
before           Execute ``X`` at the beginning of the install.
after            Execute ``X`` after all install commands.
Anything others  Execute the line (first and other columns as one line) before ``after`` is executed.
===============  ================================

If the second column is ``install``, it will be ignored.

i.e. ``brew install package`` is same as ``brew package``.

If you want to build macvim with lua option, you can write as above example ``Brewfile``.

If you use ``tap``, Brew-file only does ``tap`` the repository.

If you use ``tapall``, Brew-file does ``brew install`` for all Formulae in the repository
in addition to do ``tap`` the repository.

If you want to divide the list into several files.
If the main ``Brewfile`` has ``file`` or ``brewfile`` commands,
then corresponding argument is used as an external file.
The path can be an absolute or a relative.
If you use a relative path, like .``/Brewfile2``,
then the start directory is the directory
where the main ``Brewfile`` is.

You can use a nest of ``file``, too.
The relative path starts from the parent file's directory.

For the path, such ``~`` is translated into ``$HOME``,
and any environmental variables can be used.

e.g.

If you have::

    file ./${HOST}.Brewfile

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

You don't need to ``brew install`` by hand.
As written above, ``tap 'caskroom/cask'`` is can be dropped
because ``cask 'firefox'`` triggers it.

Some packages such macvim has Application (MacVim.app).
If you want to install them to Applications area,
please use ``-l`` (for ``~/Applications/``) or ``-g`` (for ``/Applications/``).

With ``clean`` option, Brew-file runs cleanup.
By default, it just does dry run (no actual cleanup).
To run cleanup in non dry-run mode, use ``-C``.

If you want edit ``Brewfile``, use ``edit`` option.

.. warning::

   If you do ``brew file edit`` before installing ``Brewfile`` and save w/o any modification,
   you may make empty ``Brewfile`` (Be careful, ``brew -c -C`` remove all packages :scream:).
   Therefore I recommend you to do ``brew file -i`` at first if you don't have ``Brewfile``.

You can maintain your ``Brewfile`` at the git repository.
First, make new repository at GitHub (or other git server).

Then, set the repository by::

    $ brew file set_repo -r <repository>

It will clone the repository.
If the repository has a file named ``Brewfile``, the file will be used instead of
``~/.config/brewfile/Brewfile``.
(then ``~/.config/brewfile/Brewfile`` will have this repository information.)

``repository`` should be like `rcmdnk/Brewfile <https://github.com/rcmdnk/Brewfile>`_ in GitHub,
which should have ``Brewfile`` (different file name can be used by ``-f``).

If you want to use other hosts than github, use full path for the repository, like::

    $ brew file set_repo -r git@bitbucket.org:rcmdnk/my_brewfile

If the repository doesn't have ``Brewfile`` (or specified by ``-f``, ``brew file init`` initialize the file.
Then, you can push it by ``brew file push``.

With this procedure, you can synchronize all your Mac easily :thumbsup:

To install new package, use::

    $ brew file brew install <package>

instead of ``brew install <package>``, because above command
automatically update ``Brewfile``.

This is useful especially if you are using the repository for the ``Brewfile``,
and want to use ``brew file update``.

Otherwise, please be careful to use ``brew file update``,
because it deletes what you installed, but you have not registered in ``Brewfile``.

If you want to check your Apps for Cask, use::

    $ brew file casklist

This command makes ``Caskfile.txt``, which is like::

    ### Cask applications
    ### Please copy these lines to your Brewfile and use with `brew bundle`.

    ### tap and install Cask (remove comment if necessary).
    #tap caskroom/cask
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

If you want to manage them with ``Brewfile``, just copy above lines w/o "#" for these Apps.
