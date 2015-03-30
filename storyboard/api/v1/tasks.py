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

from oslo.config import cfg
from pecan import abort
from pecan import request
from pecan import response
from pecan import rest
from pecan.secure import secure
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan

from storyboard.api.auth import authorization_checks as checks
from storyboard.api.v1.search import search_engine
from storyboard.api.v1 import validations
from storyboard.api.v1 import wmodels
from storyboard.common import decorators
from storyboard.common import exception as exc
from storyboard.db.api import milestones as milestones_api
from storyboard.db.api import tasks as tasks_api
from storyboard.db.api import timeline_events as events_api
from storyboard.openstack.common.gettextutils import _  # noqa

CONF = cfg.CONF

SEARCH_ENGINE = search_engine.get_engine()


def milestone_is_valid(milestone_id):
        milestone = milestones_api.milestone_get(milestone_id)

        if not milestone:
            raise exc.NotFound(_("Milestone %d not found.") %
                               milestone_id)

        if milestone['expired']:
            abort(400, _("Can't associate task to expired milestone."))


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

        :param task_id: An ID of the task.
        """
        task = tasks_api.task_get(task_id)

        if task:
            return wmodels.Task.from_db_model(task)
        else:
            raise exc.NotFound(_("Task %s not found") % task_id)

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose([wmodels.Task], wtypes.text, int, int, int, int, int,
                         int, [wtypes.text], [wtypes.text], int, int,
                         wtypes.text, wtypes.text)
    def get_all(self, title=None, story_id=None, assignee_id=None,
                project_id=None, project_group_id=None, branch_id=None,
                milestone_id=None, status=None, priority=None, marker=None,
                limit=None, sort_field='id', sort_dir='asc'):
        """Retrieve definitions of all of the tasks.

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
        if limit is None:
            limit = CONF.page_size_default
        limit = min(CONF.page_size_maximum, max(1, limit))

        # Resolve the marker record.
        marker_task = tasks_api.task_get(marker)

        tasks = tasks_api \
            .task_get_all(title=title,
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
                          limit=limit)
        task_count = tasks_api \
            .task_get_count(title=title,
                            story_id=story_id,
                            assignee_id=assignee_id,
                            project_id=project_id,
                            project_group_id=project_group_id,
                            branch_id=branch_id,
                            milestone_id=milestone_id,
                            status=status,
                            priority=priority)

        # Apply the query response headers.
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

        :param task: A task within the request body.
        """

        if task.creator_id and task.creator_id != request.current_user_id:
            abort(400, _("You can't select author of task."))

        if task.milestone_id:
            if task.status != 'merged':
                abort(400,
                      _("Milestones can only be associated with merged tasks"))

            milestone_is_valid(task.milestone_id)

        creator_id = request.current_user_id
        task.creator_id = creator_id

        created_task = tasks_api.task_create(task.as_dict())

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

        :param task_id: An ID of the task.
        :param task: A task within the request body.
        """

        original_task = tasks_api.task_get(task_id)

        if task.creator_id and task.creator_id != original_task.creator_id:
            abort(400, _("You can't change author of task."))

        if task.milestone_id:
            if original_task['status'] != 'merged' and task.status != 'merged':
                abort(400,
                      _("Milestones can only be associated with merged tasks"))

            if (original_task['status'] == 'merged' and
                    task.status and task.status != 'merged'):
                abort(400,
                      _("Milestones can only be associated with merged tasks"))

            milestone_is_valid(task.milestone_id)

        task_dict = task.as_dict(omit_unset=True)

        if task.status and task.status != 'merged':
            task_dict['milestone_id'] = None

        updated_task = tasks_api.task_update(task_id, task_dict)

        if updated_task:
            post_timeline_events(original_task, updated_task)
            return wmodels.Task.from_db_model(updated_task)
        else:
            raise exc.NotFound(_("Task %s not found") % task_id)

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wmodels.Task, int, status_code=204)
    def delete(self, task_id):
        """Delete this task.

        :param task_id: An ID of the task.
        """
        original_task = tasks_api.task_get(task_id)

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
    @wsme_pecan.wsexpose([wmodels.Task], wtypes.text, wtypes.text, int, int)
    def search(self, q="", marker=None, limit=None):
        """The search endpoint for tasks.

        :param q: The query string.
        :return: List of Tasks matching the query.
        """

        tasks = SEARCH_ENGINE.tasks_query(q=q,
                                          marker=marker,
                                          limit=limit)

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

        :param story_id: An ID of the story.
        :param task_id: An ID of the task.
        """
        task = tasks_api.task_get(task_id)

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
                         wtypes.text, wtypes.text)
    def get_all(self, story_id, title=None, assignee_id=None, project_id=None,
                project_group_id=None, branch_id=None, milestone_id=None,
                status=None, priority=None, marker=None, limit=None,
                sort_field='id', sort_dir='asc'):
        """Retrieve definitions of all of the tasks.

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
        if limit is None:
            limit = CONF.page_size_default
        limit = min(CONF.page_size_maximum, max(1, limit))

        # Resolve the marker record.
        marker_task = tasks_api.task_get(marker)

        tasks = tasks_api \
            .task_get_all(title=title,
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
                          limit=limit)
        task_count = tasks_api \
            .task_get_count(title=title,
                            story_id=story_id,
                            assignee_id=assignee_id,
                            project_id=project_id,
                            project_group_id=project_group_id,
                            branch_id=branch_id,
                            milestone_id=milestone_id,
                            status=status,
                            priority=priority)

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

        :param story_id: An ID of the story.
        :param task: a task within the request body.
        """

        if task.creator_id and task.creator_id != request.current_user_id:
            abort(400, _("You can't select author of task."))

        creator_id = request.current_user_id
        task.creator_id = creator_id

        if not task.story_id:
            task.story_id = story_id

        if task.story_id != story_id:
            abort(400, _("URL story_id and task.story_id do not match"))

        if task.milestone_id:
            if task.status != 'merged':
                abort(400,
                      _("Milestones can only be associated with merged tasks"))

            milestone_is_valid(task.milestone_id)

        created_task = tasks_api.task_create(task.as_dict())

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

        :param story_id: An ID of the story.
        :param task_id: An ID of the task.
        :param task: a task within the request body.
        """

        original_task = tasks_api.task_get(task_id)

        if original_task.story_id != story_id:
            abort(400, _("URL story_id and task.story_id do not match"))

        if task.creator_id and task.creator_id != original_task.creator_id:
            abort(400, _("You can't change author of task."))

        if task.milestone_id:
            if original_task['status'] != 'merged' and task.status != 'merged':
                abort(400,
                      _("Milestones can only be associated with merged tasks"))

            if (original_task['status'] == 'merged' and
                    task.status and task.status != 'merged'):
                abort(400,
                      _("Milestones can only be associated with merged tasks"))

            milestone_is_valid(task.milestone_id)

        task_dict = task.as_dict(omit_unset=True)

        if task.status and task.status != 'merged':
            task_dict['milestone_id'] = None

        updated_task = tasks_api.task_update(task_id, task_dict)

        if updated_task:
            post_timeline_events(original_task, updated_task)
            return wmodels.Task.from_db_model(updated_task)
        else:
            raise exc.NotFound(_("Task %s not found") % task_id)

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wmodels.Task, int, int, status_code=204)
    def delete(self, story_id, task_id):
        """Delete this task.

        :param story_id: An ID of the story.
        :param task_id: An ID of the task.
        """
        original_task = tasks_api.task_get(task_id)

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
