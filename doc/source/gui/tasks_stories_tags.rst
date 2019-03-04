======================
Tasks, Stories, & Tags
======================

This manual is a guide for StoryBoard users to navigate the usage of tasks, stories, and tags in the webclient.

The OpenStack StoryBoard webclient can be accessed here: https://storyboard.openstack.org.

StoryBoard is a task tracking application. It encourages anyone
to sign in and create a story.

What is a Story?
~~~~~~~~~~~~~~~~

A story is a description of something you want. Typically it is a new feature or
a bug fix.

The story describes what behavior is desired. Implementation details
are generally not inluded.

Create a Story
----------------

To create a story in StoryBoard:

#. Ensure you are logged in.

#. Find the :guilabel:`+ Create new...` button. Where this button is, varies
   a bit on the layout selected for your device (i.e. mobile or desktop).

#. Click the :guilabel:`+ Create new...` button and select :guilabel:`Story`
   from the drop down menu.

#. A pop-up window entitled :guilabel:`New Story` will appear, should you
   change your mind you can close the :guilabel:`New Story` window at any
   time by clicking the :guilabel:`X` in the top right-hand corner of the
   :guilabel:`New Story` window.

#.  Enter a title in the :guilabel:`Title:` text box.

#.  Enter a description in the :guilabel:`Description` text box.

#.  Enter a project in the text box with the :guilabel:`Select a Project`
    prompt and the magnifying glass icon.

#. These three fields are the minimum required fields for creating a story,
   once there is acceptable content in all three the :guilabel:`Save Changes`
   button will transition from greyed out to full brightness.

#. Click the :guilabel:`Save Changes` button.

#. You will see your newly created story with a default task automatically generated
   to have the same name as the story.

Private Stories
----------------

They are created the same way that regular stories are with additional steps.

#. After you've taken the first few steps to create the story- entered a title and
   description- there is a checkbox labeled 'Private or Security Vulnerability' that
   should be checked.
#. After checking the box, click the :guilabel:`Add Team or User` button to search
   for and add members of the vulnerability management team or core security
   groups. Whoever you add will be able to view the story. You will be able to view
   the story by default.

What is a Task?
~~~~~~~~~~~~~~~

A task is a piece of work to be performed, typically sized to be a single reviewable
commit. Each story requires at least one task. You cannot create a task without
associating it to a story. A task is what gets associated with a project.

Tasks also can have notes. Generally this is discussion about progress or asking for
more information or direction.


Create a Task
-------------

Add a Task to an Existing Story
===============================

#. Ensure you are logged in.

#. View an existing story.

#. Find the section in the story view entitled "Tasks", it is found below the
   story description.

#. Below the current tasks, there is a button :guilabel:`+ Add Task affecting this project`,
   button or a :guilabel:`+ Affects other project`. Depending on what task you
   are creating, click the appropriate button.

#. The :guilabel:`+ Add Task affecting this project` button will transition to
   show a :guilabel:`Enter Task Name` field and a :guilabel:`Assign user to task`
   field. You are required to at least fill in the task name field, but can fill in both.
   In most cases, a user isn't assinged at creation unless you are assigning it to yourself.
   Click save when finished. If you clicked the button :guilabel:`+ Affects other project`
   you will be prompted and required to add a project name and task name.

#. Click the :guilabel:`Save` button at the right-hand end of the row for the
   task.

#. Click the :guilabel:`- Add Task` button to close any empty task prompts.

Add a Task While Creating a Story
=================================

By default, the first task added to a newly created story is the title
of the story. To change this to describe the work rather than the goal, or
add tasks at story creation time follow these steps:

#. Ensure you are logged in.

#. Find the :guilabel:`+ Create new...` button. Where this button is, varies
   a bit on wheher you are viewing the webclient on mobile or from a desktop.

#. Click the :guilabel:`+ Create new...` button and select :guilabel:`Story`
   from the drop down menu.

#. A pop-up window entitled :guilabel:`New Story` will appear, should you
   change your mind you can close the :guilabel:`New Story` window at any
   time by clicking the :guilabel:`X` in the top right-hand corner of the
   :guilabel:`New Story` window.

#. Enter a Story title in the :guilabel:`Title:` text box.

#. Enter a Story description in the :guilabel:`Description` text box.

#. As previously stated, a task will be auto generated with the same name as
   the story. Should you want the first task to be named something other than
   the title of the new story, edit this text box until it contains your first
   task for the new story. You will also need to select a project using the
   :guilabel:`Select a Project` text box.

#. If you want to add additional tasks to this new story, click the
   :guilabel:`+ Add Another Task` button in the lower left of the
   :guilabel:`New Story` window.

#. Ensure there is content in the text box with the :guilabel:`Task Title`
   prompt and the :guilabel:`Select a Project` prompt for each task.

#. Click the :guilabel:`Save Changes` button.

#. You will see your newly created story complete with tasks.


Add notes to a Task
===================

#. Ensure you are logged in.

#. While viewing the Story with the associated task you wish to add notes to,
   find the arrow in front of the task number, click to expand. The task will
   expand to show a number of options.

#. Click the :guilabel:`Add notes` button and type the desired notes in the
   :guilabel:`Enter task notes here` text box and click the :guilabel:`Save`
   button.


What is a Tag?
~~~~~~~~~~~~~~

Tags are an easily searchable and filterable one or two word description that
help with auto populated worklists.

Adding a Tag to a Story
-----------------------

#. Ensure you are logged in.

#. View an existing story.

#. Find the section in the story view entitled "Tags", it is the middle of the
   story view.

#. Below the "Tags" heading you will see a button marked :guilabel:`Add +`,
   click this button.

#. You will see a row on the page comprised of a text box with an :guilabel:`Add`
   button and a :guilabel:`Cancel` button.

#. Add text in the text box consistent with the tag you want to use. Then click
   the :guilabel:`Add` button to include the tag on the story or click the
   :guilabel:`Cancel` button to close the add tag text box.
