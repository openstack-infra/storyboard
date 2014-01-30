Storyboard
==========

Storyboard is a task tracker for OpenStack.


-----------------
Project Resources
-----------------

Project status, bugs, and blueprints are tracked at:

  http://storyboard.openstack.org

Source code can be found at:

  https://git.openstack.org/cgit/openstack-infra/storyboard/

Documentation can be found here:

  http://ci.openstack.org/storyboard/

Additional resources are linked from the project wiki page:

  https://wiki.openstack.org/wiki/StoryBoard

Anyone wishing to contribute to an OpenStack project should
find plenty of helpful resources here:

  https://wiki.openstack.org/wiki/HowToContribute

All OpenStack projects use Gerrit for code reviews.
A good reference for that is here:

  https://wiki.openstack.org/wiki/GerritWorkflow

------------------------------
Getting Started as a Developer
------------------------------

Storyboard has two components: this API server, and the
Javascript-based web client.  To start the API server, make sure you
have the following packages installed locally:

* libpq-dev
* libmysqlclient-dev

Then run::

  mysql -u $DB_USER -p $DB_PASSWORD -e 'DROP DATABASE IF EXISTS storyboard;'
  mysql -u $DB_USER -p $DB_PASSWORD -e 'CREATE DATABASE storyboard;'
  cp ./etc/storyboard.conf.sample ./etc/storyboard.conf

Edit ./etc/storyboard.conf and set the ``connection`` parameter in the
``[database]`` section.  Then run::

  tox -e venv "storyboard-db-manage --config-file ./etc/storyboard.conf upgrade head"
  tox -e venv "storyboard-api --config-file ./etc/storyboard.conf"

Then to use the web client, clone the repo and follow the instructions
in the README::

  git clone https://git.openstack.org/openstack-infra/storyboard-webclient
