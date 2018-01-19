====================================================
Manually Upgrading/Downgrading a StoryBoard Instance
====================================================

If you have a manually deployed StoryBoard instance, for example a local
server for development, you may sometimes need to upgrade the database as
new changes are merged upstream.

Similarly, you may wish to rollback a change to for testing purposes. This
guide will explain how you can use the ``storyboard-db-manage`` tool to
upgrade and downgrade your database schema.

If using ``tox``, all commands in this guide should be run as ::

    $ tox -e venv -- $command

You may find you need to prepend ``sudo`` to this command.


Checking the current version
============================

If you don't know what version your database is currently, you can check it
with::

    $ storyboard-db-manage --config-file /path/to/storyboard.conf current


Upgrading the database
======================

If your existing database version is currently < 049, you are advised to
run the upgrade command using commit ``acce431b30a32497064ad6d1ab3872358e1e60dc``
of the storyboard repository, since after that the migrations were consolidated
and will no longer work with existing databases older than version 049.

You can upgrade to the latest database version in-place with the following
command::

    $ storyboard-db-manage --config-file /path/to/storyboard.conf upgrade head

Replacing ``head`` in this command allows you to specify a target version. For
example, this command will upgrade to version 055::

    $ storyboard-db-manage --config-file /path/to/storyboard.conf upgrade 055

It is also possible to create an sql script to upgrade the database offline::

    $ storyboard-db-manage --config-file /path/to/storyboard.conf upgrade head --sql

Additionally, you can generate a script to upgrade between two versions with::

    $ storyboard-db-manage --config-file /path/to/storyboard.conf \
        upgrade <start version>:<end version> --sql

You can also upgrade the database incrementally, by specifying the number of
revisions to apply::

    $ storyboard-db-manage --config-file /path/to/storyboard.conf \
        upgrade --delta <# of revs>


Downgrading the database
========================

If you need to downgrade to a version > 001 and < 049, you will need to first
downgrade to version 049, then use commit ``acce431b30a32497064ad6d1ab3872358e1e60dc``
to downgrade further to the version you require. After this commit, the
migrations lower than 049 were consolidated and can no longer be used
individually.

Downgrade the database by a certain number of revisions::

    $ storyboard-db-manage --config-file /path/to/storyboard.conf \
        downgrade --delta <# of revs>

You can also downgrade to a specific version::

    $ storyboard-db-manage --config-file /path/to/storyboard.conf downgrade 055

Similar to upgrading, you can use the ``--sql`` flag to generate an sql script
to be applied later.
