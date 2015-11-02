======================================
Welcome to Storyboard's documentation!
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


.. _Pecan: http://pecan.readthedocs.org/en/latest/
.. _WSME: http://wsme.readthedocs.org/en/latest/
.. _Storyboard API service: https://git.openstack.org/cgit/openstack-infra/storyboard/
.. _Storyboard Web Client: https://git.openstack.org/cgit/openstack-infra/storyboard-webclient
.. _Storyboard Python Client: https://git.openstack.org/cgit/openstack-infra/python-storyboardclient



This documentation offers information on how Storyboard works and how to
contribute to the project.


Table of contents
=================


Installation guides
-------------------
.. toctree::
   :maxdepth: 1

   install/manual
   install/development


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
* :ref:`modindex`
* :ref:`search`
