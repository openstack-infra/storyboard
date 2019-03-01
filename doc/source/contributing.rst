.. include:: ../../CONTRIBUTING.rst

.. NOTE(dhellmann): The title underline style just below relies on the
   existing format of the file included just above.

Running the Tests
-----------------

Storyboard uses tox_ to manage its unit and functional tests. After
installing tox and downloading the storyboard source the next step is
to install system dependencies. Run::

  $ tox -e bindep

Then take the listed packages and install them with your system package
manager. For example::

  $ sudo apt-get install package list here

To run the tests quickly on your local development machine you can run
the tests with the sqlite backend::

  $ tox -e sqlite

And to run the style-checker and static analysis tool::

  $ tox -e pep8

If you would like to run the test suite with proper database backends or
with python2 instead of python3 there is one more step to follow. Note
that the testsuite takes quite a bit longer to run when using the MySQL
and PostgreSQL database backends.

First ensure MySQL and PostgreSQL are running (you may need to start
these services). Then run the test-setup.sh helper script::

  $ tools/test-setup.sh

This script needs to be run with a user that has sudo access. It will
configure the databases as needed to run the unittests. You can then
runt the unittests with::

  $ tox -e py27

or for Python 3::

  $ tox -e py35

On slower systems, the database migrations may take longer than the
default timeout of 120 seconds. To override the timeout, set the
``OS_TEST_TIMEOUT`` environment variable. For example, to set the
timeout to 3 minutes, run::

  $ OS_TEST_TIMEOUT=180 tox -e py27

.. _tox: https://tox.readthedocs.io/en/latest/
