=========================
 Migrating to Storyboard
=========================

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
- If you want to run your own test migration, those directions can
  be found below in the 'Test Migration' Section


Test Migration
--------------

1. Obtain a StoryBoard instance

   First you'll need superuser permissions on a StoryBoard instance. Unless
   you are infra-core or Zara or SotK, the best way to do this is to spin
   up your own test instance in a VM or somewhere.

   There are instructions on how to do that in :doc:`/install/development`.
   I won't go into detail
   here on the ins and outs of getting set up. When you have an up-to-date
   database you'll need to log in via the webclient. Upon successfully logging
   in, connect to your database with the mysql command line client, providing
   your password as prompted::

     mysql -u $YOUR_DB_USER -p

   Then run the following::

     connect $YOUR_DB_NAME;
     update users set is_superuser=1;

   This will make every user that has so far logged in to have superuser
   permissions.

   * (optional) Obtain a sanitised dump of the production database

     If you want to test migrating against production data, you'll need that
     data. The way to obtain this is to ask an infra core nicely.

     You can use the provided .sql file to recreate the production database
     in your local instance::

       mysql -u $YOUR_DB_USER -p < /path/to/db/dump.sql

   .. warning::

      This database will have the name `storyboard`, and will obliterate
      the contents of any database you already have with the same name.

2. Create the StoryBoard project

   Log in to the webclient for your StoryBoard instance. When logged in,
   click the "Create New..." button, and pick "Project". Give the project
   a name (in storyboard.o.o this will match the git repository name, so
   you may as well use that) and a description.

   When you are happy with the name and description, and both are outlined
   in green, click "Create Project".

3. Migrate!

   You can do this with the following command::

    tox -e venv -- storyboard-migrate
      --config-file etc/storyboard.conf
      --from-project $PROJECT_IN_LAUNCHPAD
      --to-project $PROJECT_IN_STORYBOARD

   Here, `$PROJECT_IN_LAUNCHPAD` should be replaced by the name of the
   project in Launchpad, for example `monasca`. Similarly,
   `$PROJECT_IN_STORYBOARD` should be replaced the name of the project
   you are importing into in StoryBoard, for example `openstack/monasca`.

   Two parameters of the `storyboard-migrate` command
   allows for filtering by the tags associated to the bug.
   Both parameters accept a comma-separated lists of tags
   and they are mutually exclusive.

   --only-tags=tags      select only the bugs which have all
                         the specified tag(s)
   --exclude-tags=tags   exclude the bugs which have any
                         of the specified tag(s)

   Then you must wait for some time to pass whilst the project is
   migrated. You can watch the output if you like. Sometimes it will
   crash with a traceback saying the database object already exists.

   If this happens, then your migration test has FAILED and you need
   to go shout at SotK to fix this bug (or fix it yourself if you have
   the spare time to help).

   Sometimes it might break in other ways for some reason. If this
   happens, then your migration test has FAILED and you have found a
   new and exciting bug. Report it in #storyboard and maybe on
   StoryBoard somewhere and try to fix it if you like.

4. Check everything went smoothly

   At this point you have successfully run a migration. You now need to
   check that you haven't triggered any of the migration issues we know
   about currently.

   Check branches as described in 3.1, and also check that you can view
   the project page in the webclient. Page through the stories to make
   sure that none of them have content that breaks the webclient.

   Check that you can view the URL:

   http://localhost:9000/api/v1/stories?project_id=$YOUR_PROJECT_ID_HERE

   in a web browser. If there is trouble for your browser in rendering
   that then one of the stories has a non-unicode character in it which
   will ruin StoryBoard's day.

   If any of these checks don't succeed, then your migration test has
   FAILED.

   If they all succeed, then maybe so has your migration. Test everything
   you feel like testing, check some of the stories to make sure they look
   sane. Beware of things that look like a huge mess but are actually just
   our markdown parser mangling logs that weren't indented by the bug
   submitter. These aren't an issue but will probably make someone sad.

   Assuming you tested against production data and everything checked out,
   the project should be ready to migrate for real. If it wasn't tested
   against production data, now would be the time test against it as you may
   discover other bugs.

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

  .. note::

     Launchpad does not close open bugs or note the new location that
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
