# Copyright (c) 2014 Mirantis Inc.
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

from storyboard.db.api import base as api_base
from storyboard.db.api import projects as projects_api
from storyboard.db.api import stories as stories_api
from storyboard.db import models


def task_get(task_id, session=None, current_user=None):
    query = api_base.model_query(models.Task, session)
    query = query.filter(models.Task.id == task_id)

    # Filter out tasks or stories that the current user can't see
    query = query.outerjoin(models.Story)
    query = api_base.filter_private_stories(query, current_user)

    return query.first()


def task_get_all(marker=None, limit=None, sort_field=None, sort_dir=None,
                 project_group_id=None, current_user=None, **kwargs):
    # Sanity checks, in case someone accidentally explicitly passes in 'None'
    if not sort_field:
        sort_field = 'id'
    if not sort_dir:
        sort_dir = 'asc'

    # Construct the query
    query = task_build_query(project_group_id,
                             current_user=current_user,
                             **kwargs)

    query = api_base.paginate_query(query=query,
                                    model=models.Task,
                                    limit=limit,
                                    sort_key=sort_field,
                                    marker=marker,
                                    sort_dir=sort_dir)

    # Execute the query
    return query.all()


def task_get_count(project_group_id=None, current_user=None, **kwargs):
    query = task_build_query(project_group_id,
                             current_user=current_user,
                             **kwargs)

    return query.count()


def task_create(values):
    task = api_base.entity_create(models.Task, values)

    if task:
        stories_api.story_update_updated_at(task.story_id)
        # Update updated_at in projects when task is created
        projects_api.project_update_updated_at(task.project_id)
    return task


def task_update(task_id, values):
    task = api_base.entity_update(models.Task, task_id, values)
    if task:
        stories_api.story_update_updated_at(task.story_id)
        # Update updated_at in projects when task is updated
        projects_api.project_update_updated_at(task.project_id)
    return task


def task_delete(task_id):
    task = task_get(task_id)

    if task:
        stories_api.story_update_updated_at(task.story_id)
        # Update updated_at in projects when task/story is deleted
        projects_api.project_update_updated_at(task.project_id)
        api_base.entity_hard_delete(models.Task, task_id)


def task_build_query(project_group_id=None, board_id=None, worklist_id=None,
                     current_user=None, session=None, **kwargs):
    # Construct the query
    query = api_base.model_query(models.Task, session=session)

    if project_group_id:
        query = query.join(models.Project,
                           models.project_group_mapping,
                           models.ProjectGroup) \
            .filter(models.ProjectGroup.id == project_group_id)

    # Sanity check on input parameters
    query = api_base.apply_query_filters(query=query,
                                         model=models.Task,
                                         **kwargs)

    # Filter out tasks or stories that the current user can't see
    query = query.outerjoin(models.Story)
    query = api_base.filter_private_stories(query, current_user)

    if worklist_id or board_id:
        query = query.outerjoin(
            (models.WorklistItem,
             models.WorklistItem.item_id == models.Task.id))
        query = query.filter(models.WorklistItem.item_type == "task")
        query = query.outerjoin(models.Worklist)

    # Filter by worklist
    if worklist_id:
        query = query.filter(models.Worklist.id == worklist_id)
        query = api_base.filter_private_worklists(
            query, current_user, hide_lanes=False)

    # Filter by board
    if board_id:
        query = query.outerjoin(models.BoardWorklist, models.Board)
        query = api_base.filter_private_boards(query, current_user)
        query = query.filter(models.Board.id == board_id)
        query = api_base.filter_private_worklists(
            query, current_user, hide_lanes=False)

    return query


def task_get_statuses():
    return models.Task.TASK_STATUSES
