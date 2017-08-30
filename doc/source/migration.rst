Migrating to Storyboard
-----------------------
If your project is thinking about migrating to Storyboard
or has recently migrated to Storyboard, the following will
help you get started.

Planning to Migrate
-------------------
So you want to migrate...

- Talk to the storyboard team to see if your project is ready i.e.
  isn't heavily dependent on other projects, migrates into a test
  environment cleanly, etc. The #storyboard channel is a good place
  to start this conversation. We have `regular meetings
  <http://eavesdrop.openstack.org/#StoryBoard_Meeting>`_ for you to
  drop into as well
- Once it's been decided that you can migrate cleanly, pick a date
  to make the change and in the interim, try to close as many bugs
  as possible


The Migration Process
---------------------

- One patch needs to be pushed to the project-config repo to modify
  `projects.yaml <https://github.com/openstack-infra/project-config/blob/master/gerrit/projects.yaml#L255-L256>`_
  to update 'use-storyboard' to True for each of your projects in that file
- A representative from infra runs the migration scripts

Recently Migrated
-----------------

- Communicate to your project, your users and operators that bugs will now
  be filed in your `storyboard project <https://storyboard.openstack.org/>`_
  rather than launchpad project
- Lock your launchpad project so that users and operators can't file
  bugs there. In the 'Change Details' section you should update information
  about where to file bugs now, then go to the 'Bugs' section and set the
  'bugs are tracked' radio button to the 'somewhere else' option.

  NOTE: Launchpad does not close open bugs or note the new location that
  people should make comments and updates at which is why it is important
  to communicate to users, operators, and contributors that you've migrated 

Q & A
-----

- Is there integration with gerrit? Yes. `Details here.
  <https://docs.openstack.org/infra/manual/developers.html#development-workflow>`_
- What happens to bug links? Bug numbers are the story numbers and are
  used in the url for the story
- What happens to blueprints? They are not migrated because they
  are a construct tied to Launchpad. They can be optionally migrated, but
  it's not supported by default
- How do I close a task? Change the status from 'Todo' to 'merged'.
  The state of the story overall is derived from each of the tasks.
  While tasks can be complete, the story may not be done until all
  tasks are marked as 'merged' or 'invalid'. See the gerrit integration
  link above for more details
- Are there tags? Yes, anyone can add any tags to stories
- Will I be able to write scripts for it? Yes, there is a
  `REST API <https://docs.openstack.org/infra/storyboard/webapi/v1.html>`_
- Why are we using Storyboard? It was designed for the OpenStack
  use case and the ability to manage cross project efforts. It
  is managed by OpenStack and so it can be fixed and changed
  quickly.
