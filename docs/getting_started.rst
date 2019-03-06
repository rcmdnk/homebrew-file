Getting Started
===============

Use local Brewfile
------------------

By default, **Brewfile** is **~/.config/brewfile/Brewfile**.

If you don't have **Brewfile**, first, do::

    $ brew init

``brew init`` is same as ``brew file init``, if you setup ``brew-wrap`` as in :doc:`installation`.

Note: In below, ``set_repo`` command can be used directly after ``brew``,
but ``install`` or ``update`` need to use with ``brew file`` because
``brew`` command has own ``install`` or ``update`` commands.

You can check your package list by::

    $ brew file cat

If you already have **Brewfile**, then copy it to
**~/.config/brewfile/Brewfile**
and install packages listed in **Brewfile** by::

    $ brew file install

After that, you need to do only normal ``brew`` commands, like ``brew install`` or ``brew uninstall``.
After each command, **Brewfile** is updated automatically
if you set ``brew-wrap`` as in :doc:`installation`.

When you get new Mac, copy
**~/.config/brewfile** to new Mac
and just do::

    $ brew file install

Use Dropbox (or any online storages) for Brewfile management
------------------------------------------------------------

Set Brewfile place
``````````````````

You can set the place of Brewfile by using the environment variable like:

.. code-block:: sh

   export HOMEBREW_BREWFILE=~/Dropbox/Brewfile

Then, you can use Brewfile as same as the original Brewfile place.

In this case, when you have new Mac,
set ``HOMEBREW_BREWFILE`` and synchronize the file with a online storage service,
then do::

    $ brew file install

If you are using multiple Mac in the same time,
it is good to have a cron job like::

    30 12 * * * brew file update

This command installs new packages which were installed in another Mac
at a lunch time (12:30) every day.

This command also does ``brew update && brew upgrade``,
and removes packages not listed in ``Brewfile``.

If you want to do only installing new packages, then set as::

    30 12 * * * brew file install

Use GitHub (or any git repository) for Brewfile management
----------------------------------------------------------

Set up a repository
```````````````````

First, create a repository with a file named **Brewfile**.

If you use GitHub, you can make it with brew-file::

    $ brew set_repo

    Set repository,
    "non" (or empty) for local Brewfile (/Users/user/.config/brewfile/Brewfile),
    /path/to/repo for local git repository,
    https://your/git/repository (or ssh://user@server.project.git) for git repository,
    or (<user>/)<repo> for github repository,
    or full path for other git repository:

Give a name like ``rcmdnk/Brewfile`` (will be recognized as a GitHub repository),
or such ``git@github.com:rcmdnk/Brewfile``.
(or give just ``Brwefile``, if you have user name in your ``.gitconfig``.)

You can set any of other git repositories of local or other hosting sites.

For GitHub case, it will create new repository if it does not exist.

Then, initialize **Brewfile**::

    $ brew init

Set up new Mac with your Brewfile in the repository
```````````````````````````````````````````````````

Do::

    $ brew set_repo

and give your repository name.

And install packages listed in **Brewfile** like::

    $ brew file install

Brewfile management
```````````````````

To update the repository, do::

    $ brew file update

If you have set the repository,
this command does ``git pull`` and ``git push``
in addition to such brew's ``install``, ``clean``, ``update``, ``upgrade`` and removing packages
described in online storages section above.

It is good if you have such a cron job like::

    30 12 * * * brew file update

The repository is updated at lunch time every day.
