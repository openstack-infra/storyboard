================================================
 Installing and Running the Development Version
================================================

Storyboard has two components: this API server, and the
Javascript-based web client.

Launching the development VM
============================

StoryBoard has certain server dependencies which are often complicated to
install on any development environment. To simplify this,
we've provided a vagrantfile which includes all required services.

1. Install [vagrant](https://www.vagrantup.com/)
2. Install [VirtualBox](https://www.virtualbox.org/)
3. Run `vagrant up` in the storyboard root directory.

If you choose to go this route, the appropriate configuration values in
`storyboard.conf` will be as follows::

    ...

    [notifications]
    rabbit_host=127.0.0.1
    rabbit_login_method = AMQPLAIN
    rabbit_userid = storyboard
    rabbit_password = storyboard
    rabbit_port = 5672
    rabbit_virtual_host = /

    ...

    [database]
    connection = mysql+pymysql://storyboard:storyboard@127.0.0.1:3306/storyboard

    ...

Note that the VM will attempt to bind to local ports 3306, 5672,
and 15672. If those ports are already in use, you will have to modify the
vagrant file and your configuration to accommodate.

This VM has also been set up for unit tests.

Installing and Upgrading the API server
=======================================

1. To start the API server, make sure you have the following packages installed 
   locally:

   * libpq-dev
   * libmysqlclient-dev

NOTE: MySQL must be >= 5.6


2. Clone storyboard::

    git clone https://git.openstack.org/openstack-infra/storyboard
    cd storyboard


3. Add MySQL user and create database (not necessary if using VM)::

    mysql -u $DB_USER -p$DB_PASSWORD -e 'DROP DATABASE IF EXISTS storyboard;'
    mysql -u $DB_USER -p$DB_PASSWORD -e 'CREATE DATABASE storyboard;'


4. Copy the sample configuration file::

    cp ./etc/storyboard.conf.sample ./etc/storyboard.conf


5. Edit ``./etc/storyboard.conf`` and set the ``connection`` parameter in 
   the ``[database]`` section.

6. Install the correct version of tox. Latest tox has a bug. https://bugs.launchpad.net/openstack-ci/+bug/1274135::

    pip install --upgrade "tox>=1.6,<1.7"


7. Upgrade DB schema to the latest version::

    tox -e venv "storyboard-db-manage --config-file ./etc/storyboard.conf upgrade head"


8. Start the API server::

    tox -e venv "storyboard-api --config-file ./etc/storyboard.conf"


Installing the Javascript-based web client
==========================================

1. To build and start the web client, you will need either of these
   dependency sets installed locally:

   * *Option 1:*

     * Python 2.6 or 2.7
     * NodeJS v0.10.29 or newer
     * NPM v1.3.10 or newer

     (Ubuntu Trusty packages are sufficient, even though they indicate an older
     version. MySQL must be >= 5.6. )

   * *Option 2:*

     * GCC 4.2 or newer
     * Python 2.6 or 2.7
     * GNU Make 3.81 or newer
     * libexecinfo (FreeBSD and OpenBSD only)

2. Clone storyboard::

    git clone https://git.openstack.org/openstack-infra/storyboard-webclient
    cd storyboard-webclient


3. Run a local development server, which uses the localhost API::

    tox -egrunt_no_api -- serve


4. Run a local development server, which binds to a specific IP and
   consumes the localhost API::

    tox -egrunt_no_api -- serve --hostname 0.0.0.0


5. Run a local development server, which uses the production API::

    tox -egrunt_no_api -- serve:prod


Optional steps: Seed database with base data
============================================

1. If you want to define superusers in the database, copy
   ``./etc/superusers.yaml.sample`` to ``./etc/superusers.yaml`` and
   define a few superuser IDs.


2. Enable the superusers in the database::

    tox -e venv "storyboard-db-manage --config-file ./etc/storyboard.conf load_superusers ./etc/superusers.yaml"


3. If you want to quickly set up a set of projects and project groups in the
   database, copy ``./etc/projects.yaml.sample`` to ``./etc/projects.yaml``
   and define a few projects and project groups.


4. Create the projects and projectgroups in the DB::

    tox -e venv "storyboard-db-manage --config-file ./etc/storyboard.conf load_projects ./etc/projects.yaml"
