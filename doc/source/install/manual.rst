============================
 Quick Install for Operators
============================

Installing the API service
==========================

1. Install StoryBoard. [TODO: More details]


2. Storyboard only supports MySQL. Install MySQL. [TODO: details]

3. Edit ``/etc/storyboard/storyboard.conf``. You'll need to modify ``connection``
   parameter in the ``[database]`` section.

   For MySQL it will look like::

     connection = mysql://root:pass@127.0.0.1:3306/storyboard

4. Migrate database to current state::

   $ storyboard-db-manage --config-file /etc/storyboard/storyboard.conf upgrade head

5. Launch API service::

   $ storyboard-api --config-file /etc/storyboard/storyboard.conf

   .. note::

      It is recommended to use Apache+mod_wsgi for production installation.


Installing the Web Client
=========================

Grab a tarball from http://tarballs.openstack.org/storyboard-webclient, unpack
it, and serve as static files.
