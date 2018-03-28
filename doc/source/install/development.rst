=======================================
 Installing and Running for Developers
=======================================

StoryBoard has two main components: the API server, and the
Javascript-based web client. The API server is essential, but
the webclient can be swapped out for an alternative if an
alternative is available. This means it is possible to use
a different user interface with the StoryBoard API;
install instructions for those are detailed in their own repos
(eg: boartty, a commandline interface, is available here:
https://git.openstack.org/cgit/openstack/boartty/).

This install guide will cover the API and the most widely-used
StoryBoard webclient.


Installing and Upgrading the API server
=======================================

.. note::

   If you are using a Virtual Machine (VM), all commands that begin with
   ``tox`` will need to be preceeded by ``sudo``.

1. To start the API server, make sure you have the following packages installed
   locally:

   * libpq-dev
   * libmysqlclient-dev
   * python-dev
   * MySQL

     ::

       sudo apt-get update
       sudo apt-get install libpq-dev libmysqlclient-dev python-dev
       sudo apt-get install mysql-server-5.7    #Here you will be asked to set a password
       mysql --version

   .. note:: MySQL must be >= 5.6


2. Clone the StoryBoard repository::

    git clone https://git.openstack.org/openstack-infra/storyboard
    cd storyboard


3. Add MySQL user and create database:

   .. note::

      You will need to replace the ``$DB_USER`` with ``root``.  It
      will prompt for a password; this is the password you set when
      you ran ``sudo apt-get mysql-server-5.6`` in step 1.

   ::

     mysql -u $DB_USER -p -e 'DROP DATABASE IF EXISTS storyboard;'
     mysql -u $DB_USER -p -e 'CREATE DATABASE storyboard;'


4. Copy the sample configuration file::

    cp ./etc/storyboard.conf.sample ./etc/storyboard.conf


5. Edit ``./etc/storyboard.conf`` and in the ``oauth`` section, add your IP
   Adress to the list of ``valid_oauth_clients``. Then in the ``database``
   section, on the line which reads
   ``# connection = mysql+pymysql://root:pass@127.0.0.1:3306/storyboard?charset=utf8mb4``,
   replace the ``pass`` with your password (the same as used in the above
   steps). On both of these lines you will need to remove the ``#``.

6. Install tox::

     sudo apt-get install python-pip
     pip install tox

7. Upgrade DB schema to the latest version::

    tox -e venv -- storyboard-db-manage --config-file ./etc/storyboard.conf upgrade head


8. Start the API server::

    tox -e venv -- storyboard-api --config-file ./etc/storyboard.conf


Installing the Javascript-based web client
==========================================


1. To build and start the web client, you will need this dependency set
   installed locally:

   * Python 2.6 or 2.7
   * Node.js v0.10.29 or newer (see https://nodejs.org/en/download/package-manager/ for more information on getting the right package for your distribution)
   * npm v1.3.10 or newer (this will be bundled with Node.js)

   (Ubuntu Trusty packages are sufficient, even though they indicate an older
   version. MySQL must be >= 5.6.)


2. Clone the StoryBoard webclient::

    git clone https://git.openstack.org/openstack-infra/storyboard-webclient
    cd storyboard-webclient


3. Do **one** of the following that applies to you.

   a. Run a local development server, which uses the localhost API.

      ::

        tox -egrunt_no_api -- serve

   b. Run a local development server, which binds to a specific IP and
      consumes the localhost API.

      ::

        tox -egrunt_no_api -- serve --hostname 0.0.0.0

   c. Run a local development server, which uses the production API.

      ::

        tox -egrunt_no_api -- serve:prod


Make user an admin - current bug
================================

Once logged into the webclient, this user needs to be set to admin
manually due to a current bug in Storyboard.

1. Ensure that you have logged into your Storyboard instance at least once so
   that your user details are stored in the database.

2. Run mysql and change your user to superadmin::

    mysql -u root -p
    use storyboard;
    update users set is_superuser=1;


Optional steps: Seed database with base data
============================================

1. If you want to define superusers in the database, copy
   ``./etc/superusers.yaml.sample`` to ``./etc/superusers.yaml`` and
   define a few superuser IDs.


2. Enable the superusers in the database::

    tox -e venv -- storyboard-db-manage --config-file ./etc/storyboard.conf load_superusers ./etc/superusers.yaml


3. If you want to quickly set up a set of projects and project groups in the
   database, copy ``./etc/projects.yaml.sample`` to ``./etc/projects.yaml``
   and define a few projects and project groups.


4. Create the projects and projectgroups in the DB::

    tox -e venv -- storyboard-db-manage --config-file ./etc/storyboard.conf load_projects ./etc/projects.yaml


Optional steps: Set up the notifications daemon
===============================================

.. note::

   If you followed the "Launch the development VM" instuctions above,
   this step is unnecessary.

1. Install rabbitmq on your development machine::

    sudo apt-get install rabbitmq-server

2. Create a rabbitmq user/password for StoryBoard (more information
   can be found in the `rabbitmq manpages`_)::

    #                         (username) (password)
    sudo rabbitmqctl add_user storyboard storyboard
    sudo rabbitmqctl set_permissions -p / storyboard ".*" ".*" ".*"

.. _rabbitmq manpages: https://www.rabbitmq.com/man/rabbitmqctl.1.man.html#User%20management

3. Set up your storyboard.conf file for notifications using rabbitmq::

    [DEFAULT]
    enable_notifications = True

    [notifications]
    rabbit_host=127.0.0.1
    rabbit_login_method = AMQPLAIN
    rabbit_userid = storyboard
    rabbit_password = storyboard
    rabbit_port = 5672
    rabbit_virtual_host = /

4. Restart your API server (if it is running)::

    tox -e venv "storyboard-api --config-file ./etc/storyboard.conf"

5. Run the worker daemon::

    tox -e venv "storyboard-worker-daemon --config-file ./etc/storyboard.conf"
