=====================
 Installing Manually
=====================

Installing the API service
==========================

1. At the command line::

     $ pip install storyboard


   Or, if you have virtualenvwrapper installed::

     $ mkvirtualenv storyboard
     $ pip install storyboard

2. By default Storyboard will use SQLite driver which is suitable only for
   development mode. Storyboard supports MySQL and PostgreSQL backends.
   To install MySQL driver execute::

     $ pip install MySQL-python

   To install PostgreSQL driver execute::

     $ pip install psycopg2

3. Edit ``/etc/storyboard/storyboard.conf``. You'll need to modify ``connection``
   parameter in the ``[database]`` section.

   For MySQL it will look like::

     connection = mysql://root:pass@127.0.0.1:3306/storyboard

4. Migrate database to current state::

   $ storyboard-db-manage --config-file /etc/storyboard/storyboard.conf upgrade head

5. Launch API service::

   $ storyboard-api --config-file /etc/storyboard/storyboard.conf

   .. note::

      Is is recommended to use Apache+mod_wsgi for production installation.


Installing the Web Client
=========================

Web Client is an all-javascript application. It doesn't require any software to
run. Just grab tarball from http://tarballs.openstack.org/storyboard-webclient,
unpack it and serve as static files.