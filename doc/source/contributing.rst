.. include:: ../../CONTRIBUTING.rst

Running the Tests
-----------------

The test suite includes functional tests that use a MySQL database, so
you must configure a database user.

For MySQL you can use the following commands::

 mysql -u root
 mysql> CREATE USER 'openstack_citest'@'localhost' IDENTIFIED BY
        'openstack_citest';
 mysql> GRANT ALL PRIVILEGES ON * . * TO 'openstack_citest'@'localhost';
 mysql> FLUSH PRIVILEGES;

Note that the script tools/test-setup.sh can be used for the step
above.

Storyboard uses tox_ to manage its unit and functional tests. After
installing tox and downloading the storyboard source, run the tests
with::

  $ tox -e py27

or for Python 3::

  $ tox -e py35

And to run the style-checker and static analysis tool::

  $ tox -e pep8

On slower systems, the database migrations may take longer than the
default timeout of 60 seconds. To override the timeout, set the
``OS_TEST_TIMEOUT`` environment variable. For example, to set the
timeout to 2 minutes, run::

  $ OS_TEST_TIMEOUT=120 tox -e py27

.. _tox: https://tox.readthedocs.io/en/latest/
