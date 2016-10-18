# Copyright (c) 2014 Mirantis Inc.
# Copyright (c) 2016 Codethink Ltd.
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

import json
from oslo_config import cfg
from pecan import request
from pecan import response
from wsme.rest.json import tojson

from storyboard.api.v1.wmodels import TimeLineEvent
from storyboard.common import event_types
from storyboard.db.api import base as api_base
from storyboard.db.api import stories as stories_api
from storyboard.db.api import tasks as tasks_api
from storyboard.db import models
from storyboard.notifications.publisher import publish

CONF = cfg.CONF


def event_get(event_id, session=None, current_user=None):
    query = (api_base.model_query(models.TimeLineEvent, session)
        .filter_by(id=event_id))
    query = query.outerjoin(models.Story)
    query = api_base.filter_private_stories(query, current_user)

    query = query.outerjoin((
        models.Worklist,
        models.Worklist.id == models.TimeLineEvent.worklist_id))
    query = api_base.filter_private_worklists(
        query, current_user, hide_lanes=False)

    query = query.outerjoin((
        models.Board,
        models.Board.id == models.TimeLineEvent.board_id))
    query = api_base.filter_private_boards(query, current_user)

    return query.first()


def _events_build_query(current_user=None, **kwargs):
    query = api_base.model_query(models.TimeLineEvent).distinct()

    query = api_base.apply_query_filters(query=query,
                                         model=models.TimeLineEvent,
                                         **kwargs)

    query = query.outerjoin(models.Story)
    query = api_base.filter_private_stories(query, current_user)

    query = query.outerjoin((
        models.Worklist,
        models.Worklist.id == models.TimeLineEvent.worklist_id))
    query = api_base.filter_private_worklists(
        query, current_user, hide_lanes=False)

    query = query.outerjoin((
        models.Board,
        models.Board.id == models.TimeLineEvent.board_id))
    query = api_base.filter_private_boards(query, current_user)

    return query


def events_get_all(marker=None, offset=None, limit=None, sort_field=None,
                   sort_dir=None, current_user=None, **kwargs):
    if sort_field is None:
        sort_field = 'id'
    if sort_dir is None:
        sort_dir = 'asc'

    query = _events_build_query(current_user=current_user, **kwargs)
    query = api_base.paginate_query(query=query,
                                    model=models.TimeLineEvent,
                                    marker=marker,
                                    limit=limit,
                                    offset=offset,
                                    sort_key=sort_field,
                                    sort_dir=sort_dir)
    return query.all()


def events_get_count(current_user=None, **kwargs):
    query = _events_build_query(current_user=current_user, **kwargs)
    return query.count()


def event_create(values):
    new_event = api_base.entity_create(models.TimeLineEvent, values)
    if new_event:
        stories_api.story_update_updated_at(new_event.story_id)

    if CONF.enable_notifications:
        # Build the payload. Use of None is included to ensure that we don't
        # accidentally blow up the API call, but we don't anticipate it
        # happening.
        event_dict = tojson(TimeLineEvent,
                            TimeLineEvent.from_db_model(new_event))

        publish(author_id=request.current_user_id or None,
                method="POST",
                url=request.headers.get('Referer') or None,
                path=request.path or None,
                query_string=request.query_string or None,
                status=response.status_code or None,
                resource="timeline_event",
                resource_id=new_event.id or None,
                resource_after=event_dict or None)

    return new_event


def is_visible(event, user_id, session=None):
    if event is None:
        return False
    if 'worklist_contents' in event.event_type:
        event_info = json.loads(event.event_info)
        if event_info['updated'] is not None:
            info = event_info['updated']['old']
        elif event_info['removed'] is not None:
            info = event_info['removed']
        elif event_info['added'] is not None:
            info = event_info['added']
        else:
            return True

        if info.get('item_type') == 'story':
            story = stories_api.story_get_simple(
                info['item_id'], current_user=user_id, session=session)
            if story is None:
                return False
        elif info.get('item_type') == 'task':
            task = tasks_api.task_get(
                info['item_id'], current_user=user_id, session=session)
            if task is None:
                return False
    return True


def story_created_event(story_id, author_id, story_title):
    event_info = {
        "story_id": story_id,
        "story_title": story_title
    }
    return event_create({
        "story_id": story_id,
        "author_id": author_id,
        "event_type": event_types.STORY_CREATED,
        "event_info": json.dumps(event_info)
    })


def story_details_changed_event(story_id, author_id, story_title):
    event_info = {
        "story_id": story_id,
        "story_title": story_title
    }
    return event_create({
        "story_id": story_id,
        "author_id": author_id,
        "event_type": event_types.STORY_DETAILS_CHANGED,
        "event_info": json.dumps(event_info)
    })


def task_created_event(story_id, task_id, task_title, author_id):
    event_info = {
        "story_id": story_id,
        "task_id": task_id,
        "task_title": task_title
    }
    return event_create({
        "story_id": story_id,
        "author_id": author_id,
        "event_type": event_types.TASK_CREATED,
        "event_info": json.dumps(event_info)
    })


def task_status_changed_event(story_id, task_id, task_title, author_id,
                              old_status, new_status):
    event_info = {
        "story_id": story_id,
        "task_id": task_id,
        "task_title": task_title,
        "old_status": old_status,
        "new_status": new_status
    }
    return event_create({
        "story_id": story_id,
        "author_id": author_id,
        "event_type": event_types.TASK_STATUS_CHANGED,
        "event_info": json.dumps(event_info)
    })


def task_priority_changed_event(story_id, task_id, task_title, author_id,
                                old_priority, new_priority):
    event_info = {
        "story_id": story_id,
        "task_id": task_id,
        "task_title": task_title,
        "old_priority": old_priority,
        "new_priority": new_priority
    }
    return event_create({
        "story_id": story_id,
        "author_id": author_id,
        "event_type": event_types.TASK_PRIORITY_CHANGED,
        "event_info": json.dumps(event_info)
    })


def task_assignee_changed_event(story_id, task_id, task_title, author_id,
                                old_assignee_id, new_assignee_id):
    event_info = {
        "story_id": story_id,
        "task_id": task_id,
        "task_title": task_title,
        "old_assignee_id": old_assignee_id,
        "new_assignee_id": new_assignee_id
    }
    return event_create({
        "story_id": story_id,
        "author_id": author_id,
        "event_type": event_types.TASK_ASSIGNEE_CHANGED,
        "event_info": json.dumps(event_info)
    })


def task_details_changed_event(story_id, task_id, task_title, author_id):
    event_info = {
        "story_id": story_id,
        "task_id": task_id,
        "task_title": task_title
    }
    return event_create({
        "story_id": story_id,
        "author_id": author_id,
        "event_type": event_types.TASK_DETAILS_CHANGED,
        "event_info": json.dumps(event_info)
    })


def task_deleted_event(story_id, task_id, task_title, author_id):
    event_info = {
        "story_id": story_id,
        "task_id": task_id,
        "task_title": task_title
    }
    return event_create({
        "story_id": story_id,
        "author_id": author_id,
        "event_type": event_types.TASK_DELETED,
        "event_info": json.dumps(event_info)
    })


def tags_added_event(story_id, author_id, story_title, tags):
    event_info = {
        "story_id": story_id,
        "author_id": author_id,
        "story_title": story_title,
        "tags": tags
    }
    k = event_create({
        "story_id": story_id,
        "author_id": author_id,
        "story_title": story_title,
        "event_type": event_types.TAGS_ADDED,
        "event_info": json.dumps(event_info)
    })

    return k


def tags_deleted_event(story_id, author_id, story_title, tags):
    event_info = {
        "story_id": story_id,
        "author_id": author_id,
        "story_title": story_title,
        "tags": tags
    }

    return event_create({
        "story_id": story_id,
        "author_id": author_id,
        "story_title": story_title,
        "event_type": event_types.TAGS_DELETED,
        "event_info": json.dumps(event_info)
    })


def worklist_created_event(worklist_id, author_id, worklist_title):
    event_info = {
        "worklist_id": worklist_id,
        "author_id": author_id,
        "worklist_title": worklist_title
    }

    return event_create({
        "worklist_id": worklist_id,
        "author_id": author_id,
        "event_type": event_types.WORKLIST_CREATED,
        "event_info": json.dumps(event_info)
    })


def worklist_details_changed_event(worklist_id, author_id, updated, old, new):
    event_info = {
        "worklist_id": worklist_id,
        "author_id": author_id,
        "field": updated,
        "old_value": old,
        "new_value": new
    }

    return event_create({
        "worklist_id": worklist_id,
        "author_id": author_id,
        "event_type": event_types.WORKLIST_DETAILS_CHANGED,
        "event_info": json.dumps(event_info)
    })


def worklist_permission_created_event(worklist_id, author_id, permission_id,
                                      codename, users):
    event_info = {
        "worklist_id": worklist_id,
        "permission_id": permission_id,
        "author_id": author_id,
        "codename": codename,
        "users": users
    }

    return event_create({
        "worklist_id": worklist_id,
        "author_id": author_id,
        "event_type": event_types.WORKLIST_PERMISSION_CREATED,
        "event_info": json.dumps(event_info)
    })


def worklist_permissions_changed_event(worklist_id, author_id, permission_id,
                                       codename, added=[], removed=[]):
    event_info = {
        "worklist_id": worklist_id,
        "permission_id": permission_id,
        "author_id": author_id,
        "codename": codename,
        "added": added,
        "removed": removed
    }

    return event_create({
        "worklist_id": worklist_id,
        "author_id": author_id,
        "event_type": event_types.WORKLIST_PERMISSIONS_CHANGED,
        "event_info": json.dumps(event_info)
    })


def worklist_filters_changed_event(worklist_id, author_id, added=None,
                                   removed=None, updated=None):
    event_info = {
        "worklist_id": worklist_id,
        "author_id": author_id,
        "added": added,
        "removed": removed,
        "updated": updated
    }

    return event_create({
        "worklist_id": worklist_id,
        "author_id": author_id,
        "event_type": event_types.WORKLIST_FILTERS_CHANGED,
        "event_info": json.dumps(event_info)
    })


def worklist_contents_changed_event(worklist_id, author_id, added=None,
                                    removed=None, updated=None):
    event_info = {
        "worklist_id": worklist_id,
        "author_id": author_id,
        "added": added,
        "removed": removed,
        "updated": updated
    }

    return event_create({
        "worklist_id": worklist_id,
        "author_id": author_id,
        "event_type": event_types.WORKLIST_CONTENTS_CHANGED,
        "event_info": json.dumps(event_info)
    })


def board_created_event(board_id, author_id, board_title, board_description):
    event_info = {
        "board_id": board_id,
        "author_id": author_id,
        "board_title": board_title,
        "board_description": board_description
    }

    return event_create({
        "board_id": board_id,
        "author_id": author_id,
        "event_type": event_types.BOARD_CREATED,
        "event_info": json.dumps(event_info)
    })


def board_details_changed_event(board_id, author_id, updated, old, new):
    event_info = {
        "board_id": board_id,
        "author_id": author_id,
        "field": updated,
        "old_value": old,
        "new_value": new
    }

    return event_create({
        "board_id": board_id,
        "author_id": author_id,
        "event_type": event_types.BOARD_DETAILS_CHANGED,
        "event_info": json.dumps(event_info)
    })


def board_permission_created_event(board_id, author_id, permission_id,
                                   codename, users):
    event_info = {
        "board_id": board_id,
        "permission_id": permission_id,
        "author_id": author_id,
        "codename": codename,
        "users": users
    }

    return event_create({
        "board_id": board_id,
        "author_id": author_id,
        "event_type": event_types.BOARD_PERMISSION_CREATED,
        "event_info": json.dumps(event_info)
    })


def board_permissions_changed_event(board_id, author_id, permission_id,
                                    codename, added=[], removed=[]):
    event_info = {
        "board_id": board_id,
        "permission_id": permission_id,
        "author_id": author_id,
        "codename": codename,
        "added": added,
        "removed": removed
    }

    return event_create({
        "board_id": board_id,
        "author_id": author_id,
        "event_type": event_types.BOARD_PERMISSIONS_CHANGED,
        "event_info": json.dumps(event_info)
    })


def board_lanes_changed_event(board_id, author_id, added=None, removed=None,
                              updated=None):
    event_info = {
        "board_id": board_id,
        "author_id": author_id,
        "added": added,
        "removed": removed,
        "updated": updated
    }

    return event_create({
        "board_id": board_id,
        "author_id": author_id,
        "event_type": event_types.BOARD_LANES_CHANGED,
        "event_info": json.dumps(event_info)
    })
