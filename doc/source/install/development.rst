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
StoryBoard webclient, and assumes being run on Ubuntu 16.04 or
newer. The instructions are mostly portable to other distributions.

The recommended way to set up your machine for developing StoryBoard
is to use the docker-compose.yml file provided. However, we also
provide instructions for a manual setup if preferred.


Using Docker
============

This approach uses Docker to run the services required by StoryBoard,
such as MySQL and RabbitMQ. The StoryBoard API and webclient are run
on the host machine directly, to reduce cycle time when developing.
They use ``tox`` to run using virtualenvs to minimise the amount of
manual installation required.

Upon completion of these steps, you should have a usable StoryBoard
API running at ``http://localhost:8080/`` and a usable StoryBoard
webclient served at ``http://localhost:9000/``.


1. Install docker
-----------------

Follow the `docker installation instructions
<https://docs.docker.com/install/>`_ for your platform.

.. note:: On Linux, be sure to add your user to the docker group to
  avoid needing sudo::

    sudo usermod -aG docker your-user

  You'll need to log out and in again for this to take effect.


2. Install docker-compose
-------------------------

Either install using pip::

  pip3 install --user docker-compose

or follow `the instructions
<https://docs.docker.com/compose/install/>`_ for your platform.


3. Get the code
---------------

The code is stored using git, so you'll need to have git installed::

  sudo apt install git

The code for the API and webclient can then be cloned::

  git clone https://git.openstack.org/openstack-infra/storyboard
  git clone https://git.openstack.org/openstack-infra/storyboard-webclient
  cd storyboard


4. Run containers
-----------------

Currently the docker-compose.yml file sets up 3 containers to
provide the following services

- MySQL
- Swift
- RabbitMQ

The containers can be started by doing the following, starting in the
root of the ``storyboard`` repository::

  cd docker
  docker-compose up

.. note:: You can make the docker-compose process run in the background
  by instead doing::

    cd docker
    docker-compose up -d


5. Install dependencies
-----------------------

Some dependencies are needed to run the API and build the webclient. On
Ubuntu, you can install these with::

  sudo apt install build-essential python3-dev
  pip3 install --user tox


6. Migrate the database
-----------------------

At this point you could run StoryBoard, but its useless with an empty
database. The migrations are run using the ``storyboard-db-manage``
script, which you can run using tox in the root of the ``storyboard``
repository::

  tox -e venv -- storyboard-db-manage --config-file ./docker/storyboard.conf upgrade head

This command runs all the database migrations in order. Under the hood
it uses `alembic <https://alembic.sqlalchemy.org/en/latest/>`_, and
has a similar CLI.


7. Run the API
--------------

The API is run using the ``storyboard-api`` command. Again this can
be run using tox in the root of the ``storyboard`` repository::

  tox -e venv -- storyboard-api --config-file ./docker/storyboard.conf

The ``docker/storyboard.conf`` configuration file is contains config
which is already set up to use the containers created earlier, so
there is no need for manual configuration.

The output of this command should finish with something like::

  2019-03-20 11:25:44.862 22047 INFO storyboard.api.app [-] Starting server in PID 22047
  2019-03-20 11:25:44.863 22047 INFO storyboard.api.app [-] Configuration:
  2019-03-20 11:25:44.863 22047 INFO storyboard.api.app [-] serving on 0.0.0.0:8080, view at http://127.0.0.1:8080

At that point, the API is running successfully. You can stop it using
Ctrl+C or by closing your terminal.


8. Serve the webclient
----------------------

The storyboard-webclient repository provides a tox target which builds
the webclient and serves it using a development server. You can run it
using tox in the root of the ``storyboard-webclient`` repository::

  tox -e grunt_no_api -- serve

This will take a little while to run as it obtains the required dependencies
using ``npm``, and builds node-sass.

The output of this command should finish with something like::

  Running "connect:livereload" (connect) task
  Started connect web server on http://localhost:9000

  Running "watch" task
  Waiting...

At that point the webclient is being served successfully. You can stop it
using Ctrl+C or by closing the terminal. Any changes to existing files in
the codebase will cause it to automatically rebuild the webclient and
refresh the page in your browser, to help streamline the development
workflow.

You can view it in a browser at ``http://localhost:9000/``. You should also
be able to log in here. The provided configuration file uses Ubuntu One as
the OpenID provider, so you'll need an Ubuntu One account to do so.


9. Enable notifications
-----------------------

Notifications in StoryBoard are handled by workers which subscribe to
events on a message queue. Currently only RabbitMQ is supported. The
docker-compose.yml file runs a RabbitMQ server, and the provided config
file is already set up to enable notifications.

To run the workers so that notifications are actually created, use tox
in the root of the ``storyboard`` repository::

  tox -e storyboard-worker-daemon --config-file ./docker/storyboard.conf

This will start 5 workers to listen for events and create any relevant
notifications.


Installing and Upgrading the API server
=======================================

1. To start the API server, make sure you have the following packages installed
   locally:

   * build-essential
   * python3-dev
   * python3-pip
   * MySQL

     ::

       sudo apt update
       sudo apt install build-essential python3-dev python3-pip
       sudo apt install mysql-server-5.7    # Here you will be asked to set a password
       mysql --version

   .. note:: MySQL must be >= 5.6, to support fulltext indexes on InnoDB tables


2. Clone the StoryBoard repository::

    git clone https://git.openstack.org/openstack-infra/storyboard
    cd storyboard


3. Create database:

   .. note::

      You will need to replace the ``$DB_USER`` with ``root``.  It
      will prompt for a password; this is the password you set when
      you ran ``sudo apt-get mysql-server-5.7`` in step 1.

   ::

     mysql -u $DB_USER -p -e 'DROP DATABASE IF EXISTS storyboard;'
     mysql -u $DB_USER -p -e 'CREATE DATABASE storyboard;'


4. Copy the sample configuration file::

    cp ./etc/storyboard.conf.sample ./etc/storyboard.conf


5. Edit ``./etc/storyboard.conf`` and make the following changes:

   * in the ``oauth`` section, add your IP Address to the list of ``valid_oauth_clients``
   * in the ``database`` section, on the line which reads
     ``# connection = mysql+pymysql://root:pass@127.0.0.1:3306/storyboard?charset=utf8mb4``,
     replace the ``pass`` with your password (the same as used in the above
     steps)

   Uncomment both of these lines by removing the ``#``.


6. Install tox::

     sudo pip3 install tox


7. Upgrade DB schema to the latest version::

    tox -e venv -- storyboard-db-manage --config-file ./etc/storyboard.conf upgrade head


8. Start the API server::

    tox -e venv -- storyboard-api --config-file ./etc/storyboard.conf


Installing the Javascript-based web client
==========================================


1. To build and start the web client, you will need this dependency set
   installed locally:

   * tox
   * Node.js v0.10.29 or newer (see https://nodejs.org/en/download/package-manager/
     for more information on getting the right package for your distribution)
   * npm v1.3.10 or newer (this will be bundled with Node.js)


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


Using your development StoryBoard
=================================

Once the API and the webclient development server are running, you can
use your development instance of StoryBoard in a few ways.

By default, the webclient development server uses port 9000, and so
can be accessed by navigating to `http://localhost:9000/` in a web browser.
In order to log in, the hostname or IP address being used here will need to
be in the `valid_oauth_clients` key of `./etc/storyboard.conf` for the API.

By default, the API server uses port 8080, and so the API can be accessed
at `http://localhost:8080/`. That will produce a 404 as the API doesn't
actually serve anything on the `/` endpoint. The API endpoints that are
available are documented on the :doc:`../webapi/v1` page.

The webclient server also forwards `/api` to the API server, so it is also
possible to use the API by sending requests to `http://localhost:9000/api/`.


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

1. Install rabbitmq on your development machine::

    sudo apt install rabbitmq-server

2. Create a rabbitmq user/password for StoryBoard (more information
   can be found in the `rabbitmq manpages`_)::

    #                         (username) (password)
    sudo rabbitmqctl add_user storyboard storyboard
    sudo rabbitmqctl set_permissions -p / storyboard ".*" ".*" ".*"

.. _rabbitmq manpages: https://www.rabbitmq.com/rabbitmqctl.8.html#User_Management

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
