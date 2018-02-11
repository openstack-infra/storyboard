# Copyright (c) 2013 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import copy
from oslo_config import cfg
from pecan import abort
from pecan import request
from pecan import response
from pecan import rest
from pecan.secure import secure
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan

from storyboard._i18n import _
from storyboard.api.auth import authorization_checks as checks
from storyboard.api.v1.search import search_engine
from storyboard.api.v1 import validations
from storyboard.api.v1 import wmodels
from storyboard.common import decorators
from storyboard.common import exception as exc
from storyboard.db.api import branches as branches_api
from storyboard.db.api import milestones as milestones_api
from storyboard.db.api import stories as stories_api
from storyboard.db.api import story_types as story_types_api
from storyboard.db.api import tasks as tasks_api
from storyboard.db.api import timeline_events as events_api

CONF = cfg.CONF

SEARCH_ENGINE = search_engine.get_engine()


def milestone_is_valid(task):
    """Check that milestone exists, milestone and task associated with the
    same branch and milestone is not expired.
    """

    milestone_id = task.milestone_id
    milestone = milestones_api.milestone_get(milestone_id)

    if not milestone:
        raise exc.NotFound(_("Milestone %s not found.") %
                           milestone_id)

    if milestone['expired']:
        abort(400, _("You can't associate task to expired milestone %s.")
              % milestone_id)

    if task.branch_id and milestone.branch_id != task.branch_id:
        abort(400, _("Milestone %(m_id)s doesn't associate "
                     "with branch %(b_id)s.")
              % {'m_id': milestone_id, 'b_id': task.branch_id})


def branch_is_valid(task):
    """Check that branch exists, branch and task associated with the same
    project and branch is not expired.
    """

    branch = branches_api.branch_get(task.branch_id)

    if not branch:
        raise exc.NotFound(_("Branch %s not found.") % task.branch_id)

    if branch.project_id != task.project_id:
        abort(400, _("Branch %(b_id)s doesn't associate with "
                     "project %(p_id)s.")
              % {'b_id': branch.id, 'p_id': task.project_id})

    if branch["expired"]:
        abort(400, _("You can't associate task with expired branch %s.") %
              task.branch_id)

    return branch


def story_is_valid(task, branch):
    """Check that branch is restricted if story type is restricted.
    """

    story = stories_api.story_get(
        task.story_id, current_user=request.current_user_id)

    if not story:
        raise exc.NotFound("Story %s not found." % task.story_id)

    story_type = story_types_api.story_type_get(story.story_type_id)

    if story_type.restricted:
        if not branch.restricted:
            abort(400, _("Branch %s must be restricted.") % branch.id)


def task_is_valid_post(task):
    """Check that task can be created.
    """

    # Check that task author didn't change creator_id.
    if task.creator_id and task.creator_id != request.current_user_id:
        abort(400, _("You can't select author of task."))

    # Check that project_id is in request
    if not task.project_id:
        abort(400, _("You must select a project for task."))

    # Check that story_id is in request
        if not task.story_id:
            abort(400, _("You must select a story for task."))

    # Set branch_id to 'master' branch defaults and check that
    # branch is valid for this task.
    branch = None

    if not task.branch_id:
        branch = branches_api.branch_get_master_branch(
            task.project_id
        )
        task.branch_id = branch.id
    else:
        branch = branch_is_valid(task)

    # Check that branch is restricted if story type is restricted
    story_is_valid(task, branch)

    # Check that task status is merged and milestone is valid for this task
    # if milestone_id is in request.
    if task.milestone_id:
        if task.status != 'merged':
            abort(400,
                  _("Milestones can only be associated with merged tasks"))

        milestone_is_valid(task)

    return task


def task_is_valid_put(task, original_task):
    """Check that task can be update.
    """

    # Check that creator_id of task can't be changed.
    if task.creator_id and task.creator_id != original_task.creator_id:
        abort(400, _("You can't change author of task."))

    # Set project_id if it isn't in request.
    if not task.project_id:
        task.project_id = original_task.project_id

    # Set branch_id if it isn't in request.
    if not task.branch_id:
        task.branch_id = original_task.branch_id

    # Check that branch is valid for this task. If project_id was changed,
    # task will be associated with master branch of this project, because
    # client doesn't support branches.
    if task.project_id == original_task.project_id:
        branch_is_valid(task)
    else:
        task.branch_id = branches_api.branch_get_master_branch(
            task.project_id
        ).id

    # Check that task ready to associate with milestone if milestone_id in
    # request.
    if task.milestone_id:
        if original_task.status != 'merged' and task.status != 'merged':
            abort(400,
                  _("Milestones can only be associated with merged tasks"))

        if (original_task.status == 'merged' and
                task.status and task.status != 'merged'):
            abort(400,
                  _("Milestones can only be associated with merged tasks"))
    elif 'milestone_id' in task.as_dict(omit_unset=True):
        return task

    # Set milestone id if task status isn't 'merged' or if original task
    # has milestone_id.
    if task.status and task.status != 'merged':
        task.milestone_id = None
    elif not task.milestone_id and original_task.milestone_id:
        task.milestone_id = original_task.milestone_id

    # Check that milestone is valid for this task.
    if task.milestone_id:
        milestone_is_valid(task)

    return task


def post_timeline_events(original_task, updated_task):
        # If both the assignee_id and the status were changed there will be
        # two separate comments in the activity log.

        author_id = request.current_user_id
        specific_change = False

        if original_task.status != updated_task.status:
            events_api.task_status_changed_event(
                story_id=original_task.story_id,
                task_id=original_task.id,
                task_title=original_task.title,
                author_id=author_id,
                old_status=original_task.status,
                new_status=updated_task.status)
            specific_change = True

        if original_task.priority != updated_task.priority:
            events_api.task_priority_changed_event(
                story_id=original_task.story_id,
                task_id=original_task.id,
                task_title=original_task.title,
                author_id=author_id,
                old_priority=original_task.priority,
                new_priority=updated_task.priority)
            specific_change = True

        if original_task.assignee_id != updated_task.assignee_id:
            events_api.task_assignee_changed_event(
                story_id=original_task.story_id,
                task_id=original_task.id,
                task_title=original_task.title,
                author_id=author_id,
                old_assignee_id=original_task.assignee_id,
                new_assignee_id=updated_task.assignee_id)
            specific_change = True

        if not specific_change:
            events_api.task_details_changed_event(
                story_id=original_task.story_id,
                task_id=original_task.id,
                task_title=original_task.title,
                author_id=author_id)


class TasksPrimaryController(rest.RestController):
    """Manages tasks."""

    _custom_actions = {"search": ["GET"]}

    validation_post_schema = validations.TASKS_POST_SCHEMA
    validation_put_schema = validations.TASKS_PUT_SCHEMA

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose(wmodels.Task, int)
    def get_one(self, task_id):
        """Retrieve details about one task.

        Example::

          curl https://my.example.org/api/v1/tasks/24

        :param task_id: An ID of the task.
        """
        task = tasks_api.task_get(
            task_id, current_user=request.current_user_id)

        if task:
            return wmodels.Task.from_db_model(task)
        else:
            raise exc.NotFound(_("Task %s not found") % task_id)

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose([wmodels.Task], wtypes.text, int, int, int, int, int,
                         int, [wtypes.text], [wtypes.text], int, int,
                         wtypes.text, wtypes.text, wtypes.text)
    def get_all(self, title=None, story_id=None, assignee_id=None,
                project_id=None, project_group_id=None, branch_id=None,
                milestone_id=None, status=None, priority=None, marker=None,
                limit=None, link=None, sort_field='id', sort_dir='asc'):
        """Retrieve definitions of all of the tasks.

        Example::

          curl https://my.example.org/api/v1/tasks

        :param title: Search by task title.
        :param story_id: Filter tasks by story ID.
        :param assignee_id: Filter tasks by who they are assigned to.
        :param project_id: Filter the tasks based on project.
        :param project_group_id: Filter tasks based on project group.
        :param branch_id: Filter tasks based on branch_id.
        :param milestone_id: Filter tasks based on milestone.
        :param status: Filter tasks by status.
        :param priority: Filter tasks by priority.
        :param marker: The resource id where the page should begin.
        :param limit: The number of tasks to retrieve.
        :param sort_field: The name of the field to sort on.
        :param sort_dir: Sort direction for results (asc, desc).
        """

        # Boundary check on limit.
        if limit is not None:
            limit = max(0, limit)

        # Resolve the marker record.
        marker_task = tasks_api.task_get(marker)

        tasks = tasks_api \
            .task_get_all(title=title,
                          link=link,
                          story_id=story_id,
                          assignee_id=assignee_id,
                          project_id=project_id,
                          project_group_id=project_group_id,
                          branch_id=branch_id,
                          milestone_id=milestone_id,
                          status=status,
                          priority=priority,
                          sort_field=sort_field,
                          sort_dir=sort_dir,
                          marker=marker_task,
                          limit=limit,
                          current_user=request.current_user_id)
        task_count = tasks_api \
            .task_get_count(title=title,
                            link=link,
                            story_id=story_id,
                            assignee_id=assignee_id,
                            project_id=project_id,
                            project_group_id=project_group_id,
                            branch_id=branch_id,
                            milestone_id=milestone_id,
                            status=status,
                            priority=priority,
                            current_user=request.current_user_id)

        # Apply the query response headers.
        if limit:
            response.headers['X-Limit'] = str(limit)
        response.headers['X-Total'] = str(task_count)
        if marker_task:
            response.headers['X-Marker'] = str(marker_task.id)

        return [wmodels.Task.from_db_model(s) for s in tasks]

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wmodels.Task, body=wmodels.Task)
    def post(self, task):
        """Create a new task.

        Example::

          curl https://my.example.org/api/v1/tasks \\
          -H 'Authorization: Bearer MY_ACCESS_TOKEN' \\
          -H 'Content-Type: application/json;charset=UTF-8' \\
          --data-binary '{"story_id":19,"title":"Task Foo",\\
                          "project_id":153,"status":"todo"}'

        :param task: a task within the request body.
        """

        task = task_is_valid_post(task)

        creator_id = request.current_user_id
        task.creator_id = creator_id

        # We can't set due dates when creating tasks at the moment.
        task_dict = task.as_dict()
        if "due_dates" in task_dict:
            del task_dict['due_dates']

        created_task = tasks_api.task_create(task_dict)

        events_api.task_created_event(story_id=task.story_id,
                                      task_id=created_task.id,
                                      task_title=created_task.title,
                                      author_id=creator_id)

        return wmodels.Task.from_db_model(created_task)

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wmodels.Task, int, body=wmodels.Task)
    def put(self, task_id, task):
        """Modify this task.

        Example::

          curl https://my.example.org/api/v1/tasks -X PUT \\
          -H 'Authorization: Bearer MY_ACCESS_TOKEN' \\
          -H 'Content-Type: application/json;charset=UTF-8' \\
          --data-binary '{"task_id":27,"status":"merged"}'

        :param task_id: An ID of the task.
        :param task: A task within the request body.
        """

        original_task = copy.deepcopy(
            tasks_api.task_get(task_id, current_user=request.current_user_id))

        if not original_task:
            raise exc.NotFound(_("Task %s not found.") % task_id)

        task = task_is_valid_put(task, original_task)

        updated_task = tasks_api.task_update(task_id, task.as_dict(
            omit_unset=True))

        post_timeline_events(original_task, updated_task)
        return wmodels.Task.from_db_model(updated_task)

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(None, int, status_code=204)
    def delete(self, task_id):
        """Delete this task.

        Example::

          curl https://my.example.org/api/v1/tasks/27 -X DELETE \\
          -H 'Authorization: Bearer MY_ACCESS_TOKEN'

        :param task_id: An ID of the task.
        """
        original_task = copy.deepcopy(
            tasks_api.task_get(task_id, current_user=request.current_user_id))

        if not original_task:
            raise exc.NotFound(_("Task %s not found.") % task_id)

        events_api.task_deleted_event(
            story_id=original_task.story_id,
            task_id=original_task.id,
            task_title=original_task.title,
            author_id=request.current_user_id)

        tasks_api.task_delete(task_id)

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose([wmodels.Task], wtypes.text, int, int, int, int, int,
                         int, [wtypes.text], int, int, wtypes.text,
                         wtypes.text)
    def search(self, q="", story_id=None, assignee_id=None,
               project_id=None, project_group_id=None, branch_id=None,
               milestone_id=None, status=None, offset=None, limit=None,
               sort_field='id', sort_dir='asc'):
        """Search and filter the tasks.

        Example::

          curl https://my.example.org/api/v1/tasks/search?q=mary

        :param q: Fulltext search query parameter.
        :param story_id: Filter tasks by story ID.
        :param assignee_id: Filter tasks by who they are assigned to.
        :param project_id: Filter the tasks based on project.
        :param project_group_id: Filter tasks based on project group.
        :param branch_id: Filter tasks based on branch_id.
        :param milestone_id: Filter tasks based on milestone.
        :param status: Filter tasks by status.
        :param offset: The offset to start the results at.
        :param limit: The number of tasks to retrieve.
        :param sort_field: The name of the field to sort on.
        :param sort_dir: Sort direction for results (asc, desc).
        :return: List of Tasks matching the query.
        """

        user = request.current_user_id
        tasks = SEARCH_ENGINE.tasks_query(
            q=q,
            story_id=story_id,
            assignee_id=assignee_id,
            project_id=project_id,
            project_group_id=project_group_id,
            branch_id=branch_id,
            milestone_id=milestone_id,
            status=status,
            sort_field=sort_field,
            sort_dir=sort_dir,
            offset=offset,
            limit=limit,
            current_user=user)

        return [wmodels.Task.from_db_model(task) for task in tasks]


class TasksNestedController(rest.RestController):
    """Manages tasks through the /stories/<story_id>/tasks endpoint."""

    validation_post_schema = validations.TASKS_POST_SCHEMA
    validation_put_schema = validations.TASKS_PUT_SCHEMA

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose(wmodels.Task, int, int)
    def get_one(self, story_id, task_id):
        """Retrieve details about one task.

        Example::

          curl https://my.example.org/api/v1/stories/11/tasks/2691

        :param story_id: An ID of the story.
        :param task_id: An ID of the task.
        """
        task = tasks_api.task_get(
            task_id, current_user=request.current_user_id)

        if task:
            if task.story_id != story_id:
                abort(400, _("URL story_id and task.story_id do not match"))
            return wmodels.Task.from_db_model(task)
        else:
            raise exc.NotFound(_("Task %s not found") % task_id)

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose([wmodels.Task], int, wtypes.text, int, int, int, int,
                         int, [wtypes.text], [wtypes.text], int, int,
                         wtypes.text, wtypes.text, wtypes.text)
    def get_all(self, story_id, title=None, assignee_id=None, project_id=None,
                project_group_id=None, branch_id=None, milestone_id=None,
                status=None, priority=None, marker=None, limit=None,
                sort_field='id', sort_dir='asc', link=None):
        """Retrieve definitions of all of the tasks associated with a story.

        Example::

          curl https://my.example.org/api/v1/stories/11/tasks

        :param story_id: filter tasks by story ID.
        :param title: search by task title.
        :param assignee_id: filter tasks by who they are assigned to.
        :param project_id: filter the tasks based on project.
        :param project_group_id: filter tasks based on project group.
        :param branch_id: filter tasks based on branch_id.
        :param milestone_id: filter tasks based on milestone.
        :param status: filter tasks by status.
        :param priority: filter tasks by priority.
        :param marker: The resource id where the page should begin.
        :param limit: The number of tasks to retrieve.
        :param sort_field: The name of the field to sort on.
        :param sort_dir: sort direction for results (asc, desc).
        """

        # Boundary check on limit.
        if limit is not None:
            limit = max(0, limit)

        # Resolve the marker record.
        marker_task = tasks_api.task_get(
            marker, current_user=request.current_user_id)

        tasks = tasks_api \
            .task_get_all(title=title,
                          link=link,
                          story_id=story_id,
                          assignee_id=assignee_id,
                          project_id=project_id,
                          project_group_id=project_group_id,
                          branch_id=branch_id,
                          milestone_id=milestone_id,
                          status=status,
                          priority=priority,
                          sort_field=sort_field,
                          sort_dir=sort_dir,
                          marker=marker_task,
                          limit=limit,
                          current_user=request.current_user_id)
        task_count = tasks_api \
            .task_get_count(title=title,
                            link=link,
                            story_id=story_id,
                            assignee_id=assignee_id,
                            project_id=project_id,
                            project_group_id=project_group_id,
                            branch_id=branch_id,
                            milestone_id=milestone_id,
                            status=status,
                            priority=priority,
                            current_user=request.current_user_id)

        # Apply the query response headers.
        response.headers['X-Limit'] = str(limit)
        response.headers['X-Total'] = str(task_count)
        if marker_task:
            response.headers['X-Marker'] = str(marker_task.id)

        return [wmodels.Task.from_db_model(s) for s in tasks]

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wmodels.Task, int, body=wmodels.Task)
    def post(self, story_id, task):
        """Create a new task.

        Example::

          curl 'https://my.example.org/api/v1/stories/19/tasks' \\
          -H 'Authorization: Bearer MY_ACCESS_TOKEN' \\
          -H 'Content-Type: application/json;charset=UTF-8' \\
          --data-binary '{"title":"Task Foo","project_id":153,"key":"todo"}'

        :param story_id: An ID of the story.
        :param task: a task within the request body.
        """

        if not task.story_id:
            task.story_id = story_id

        if task.story_id != story_id:
            abort(400, _("URL story_id and task.story_id do not match"))

        task = task_is_valid_post(task)

        creator_id = request.current_user_id
        task.creator_id = creator_id

        # We can't set due dates when creating tasks at the moment.
        task_dict = task.as_dict()
        if "due_dates" in task_dict:
            del task_dict['due_dates']

        created_task = tasks_api.task_create(task_dict)

        events_api.task_created_event(story_id=task.story_id,
                                      task_id=created_task.id,
                                      task_title=created_task.title,
                                      author_id=creator_id)

        return wmodels.Task.from_db_model(created_task)

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wmodels.Task, int, int, body=wmodels.Task)
    def put(self, story_id, task_id, task):
        """Modify this task.

        Example::

          curl 'https://my.example.org/api/v1/stories/19/tasks/19' -X PUT \\
          -H 'Authorization: Bearer MY_ACCESS_TOKEN' \\
          -H 'Content-Type: application/json;charset=UTF-8' \\
          --data-binary '{"title":"Task Foio","project_id":153,"key":"todo"}'

        :param story_id: An ID of the story.
        :param task_id: An ID of the task.
        :param task: a task within the request body.
        """

        original_task = copy.deepcopy(
            tasks_api.task_get(task_id, current_user=request.current_user_id))

        if not original_task:
            raise exc.NotFound(_("Task %s not found") % task_id)

        if original_task.story_id != story_id:
            abort(400, _("URL story_id and task.story_id do not match"))

        if task.story_id and original_task.story_id != task.story_id:
            abort(
                400,
                _("the story_id of a task cannot be changed through this API"),
            )

        task = task_is_valid_put(task, original_task)

        updated_task = tasks_api.task_update(task_id, task.as_dict(
            omit_unset=True))

        post_timeline_events(original_task, updated_task)
        return wmodels.Task.from_db_model(updated_task)

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(None, int, int, status_code=204)
    def delete(self, story_id, task_id):
        """Delete this task.

        Example::

          curl 'https://my.example.org/api/v1/stories/11/tasks/28' -X DELETE \\
          -H 'Authorization: Bearer MY_ACCESS_TOKEN'

        :param story_id: An ID of the story.
        :param task_id: An ID of the task.
        """

        original_task = copy.deepcopy(
            tasks_api.task_get(task_id, current_user=request.current_user_id))

        if not original_task:
            raise exc.NotFound(_("Task %s not found.") % task_id)

        if original_task.story_id != story_id:
            abort(400, _("URL story_id and task.story_id do not match"))

        events_api.task_deleted_event(
            story_id=original_task.story_id,
            task_id=original_task.id,
            task_title=original_task.title,
            author_id=request.current_user_id)

        tasks_api.task_delete(task_id)
