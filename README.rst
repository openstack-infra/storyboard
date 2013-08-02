==============================================================
StoryBoard - A task tracking system for inter-related projects
==============================================================

StoryBoard is the Django app (leveraging Bootstrap at the presentation layer)
for task tracking across inter-related projects. It is meant to be suitable
for OpenStack task tracking.

Features
========

At this stage, StoryBoard is just a proof-of-concept to see if it's worth
investing more into developing it.

Current features
----------------

*Bug tracking*
  Like Launchpad Bugs, StoryBoard implements bugs as stories, with tasks that
  may affect various project/branch combinations. You can currently create
  bugs, tasks for bugs, edit their status, comment on them, etc. The current
  POC is incomplete: it does not do any sort of form client-side validation,
  and is missing search features, pagination, results ordering. This should
  definitely be improved if we go forward with this.

*Project views*
  Basic project views that let you retrieve the list of tasks for a given
  project, as well as an example of a workflow-oriented view (the 'Triage
  bugs' view). The current POC is is also just a minimal stub of the project
  view feature set.

*Markdown descriptions and comments*
  Story descriptions and comments can use markdown for richer interaction.


Questionable features
---------------------

Some current design choices are questionable and open to discussion:

Priority is set for the whole story
  Instead of each task having their own priority, the story itself has a
  priority. It makes triaging easier, however we may want to be able to have
  tasks with various priorities within a single story...

No invalid/wontfix/opinion status
  We delete tasks rather than marking them invalid. On the benefits side, that
  means there is only one way to do it, on the drawbacks side you have to look
  into history to see if a given project task was considered and abandoned...


Future features
---------------

*Feature tracking*
  The equivalent of Launchpad Blueprints, they inherit the same 'story'
  framework as bugs. That means they don't have most of the limitations of
  LP blueprints: you can comment in them, you can have tasks affecting multiple
  projects, you can even have multiple tasks affecting the same project and
  order them !

*Project groups*
  Projects can be grouped together arbitrarily, and all 'project' views can
  be reused by project groups. That makes it easy to triage or track all
  tasks for projects within a given OpenStack program.

*Subscription*
  Users should be able to subscribe to tasks (and get them in a specific view)
  as well as subscribe to projects (have their own customized project group).
  This lets you easily get customized views for the stuff that happens to
  matters to you, personally.

*Gerrit integration*
  StoryBoard should reuse the projects and groups defined for Gerrit. It should
  reflect merges with deeper integration than with LP... potentially forcing
  a 1:1 relationship between tasks and merges (one merge = one task marked
  'Landed')

*Development cycle tracking*
  A new tab for StoryBoard, giving you per-cycle and per-milestone views of
  progress. Would replace the need for status.o.o/releasestatus. Cycles and
  milestones could be specified per project, although having a default, common
  set would avoid duplication (and allow cross-project milestone views).

See https://github.com/ttx/storyboard/issues for more feature backlog.


Install, test and run
=====================

Prerequisites
-------------

You'll need the following Python modules installed:
 - django (1.4+)
 - django-openid-auth
 - markdown
 - python-openid

You can get them by running::

  pip install -r requirements.txt

Configuration and DB creation
-----------------------------

Copy storyboard/local_settings.py.sample to storyboard/local_settings.py
and change settings there.

Create empty database, create default admin user:
./manage.py syncdb


Basic test using Django development server
------------------------------------------

Run Django development server:
./manage.py runserver

Create basic data via the admin interface: http://127.0.0.1:8000/admin,
using the admin credentials above.

At least:
 * a master branch
 * a release branch
 * a milestone associated with the master branch
  - the milestone also has to have the undefined box checked
 * a project

Then log out and access the application at:
http://127.0.0.1:8000/
