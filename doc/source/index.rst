======================================
Welcome to StoryBoard's documentation!
======================================

Introduction
============

StoryBoard is a web application for task tracking across inter-related projects.
It is meant to be suitable for OpenStack task tracking.

StoryBoard consists of two components:
    * `Storyboard API service`_ - is a Python application leveraging
      `Pecan`_/`WSME`_ for REST API layer
    * `Storyboard Web Client`_ - is an all-javascript webclient for the
      Storyboard API


.. _Pecan: https://pecan.readthedocs.io/en/latest/
.. _WSME: https://wsme.readthedocs.io/en/latest/
.. _Storyboard API service: https://git.openstack.org/cgit/openstack-infra/storyboard/
.. _Storyboard Web Client: https://git.openstack.org/cgit/openstack-infra/storyboard-webclient
.. _Storyboard Python Client: https://git.openstack.org/cgit/openstack-infra/python-storyboardclient



This documentation offers information on how to use StoryBoard,
how StoryBoard works and how to contribute to the project.


Table of contents
=================

Using StoryBoard
----------------

.. toctree::
   :maxdepth: 1

   How it Works <gui/theory>
   Boards <gui/boards>
   Worklists <gui/worklists>
   Tasks, Stories, & Tags <gui/tasks_stories_tags>
   Organizing Your Work: Best Practices <gui/best_practices>

Installation guides
-------------------
.. toctree::
   :maxdepth: 1

   install/development

Maintenance guides
------------------
.. toctree::
   :maxdepth: 1

   maintenance/upgrading


Launchpad Migration guides
--------------------------
.. toctree::
   :maxdepth: 1

   migration

Developer docs
--------------

.. toctree::
   :maxdepth: 1

   contributing
   webclient

Extending StoryBoard
--------------------

.. toctree::
   :maxdepth: 1

   Overview <extending/index>
   Plugins: Cron Workers <extending/plugin_cron>
   Plugins: Event Workers <extending/plugin_worker>


Client API Reference
--------------------

.. toctree::
   :maxdepth: 1

   webapi/v1

Indices and tables
==================

* :ref:`genindex`
* :ref:`search`
