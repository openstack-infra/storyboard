================================================
 Installing and Running the Development Version
================================================

Storyboard has two components: this API server, and the
Javascript-based web client.


Installing the API server
=========================

1. To start the API server, make sure you have the following packages installed 
   locally:

   * libpq-dev
   * libmysqlclient-dev


2. Clone storyboard::

	git clone https://git.openstack.org/openstack-infra/storyboard
	cd storyboard


3. Add MySQL user and create database::

   	mysql -u $DB_USER -p $DB_PASSWORD -e 'DROP DATABASE IF EXISTS storyboard;'
   	mysql -u $DB_USER -p $DB_PASSWORD -e 'CREATE DATABASE storyboard;'


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

1. To build and start the web client, make sure you have the following packages 
   installed locally:

   * Xvfb
   * GCC 4.2 or newer
   * Python 2.6 or 2.7
   * GNU Make 3.81 or newer
   * libexecinfo (FreeBSD and OpenBSD only)


2. Clone storyboard::

   	git clone https://git.openstack.org/openstack-infra/storyboard-webclient
   	cd storyboard-webclient


3. Run a local development server::

   	tox -egrunt_no_api server


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
