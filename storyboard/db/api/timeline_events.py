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

import json
from oslo.config import cfg
from pecan import request
from pecan import response

from storyboard.common import event_types
from storyboard.db.api import base as api_base
from storyboard.db import models
from storyboard.notifications.publisher import publish

CONF = cfg.CONF


def event_get(event_id):
    return api_base.entity_get(models.TimeLineEvent, event_id)


def events_get_all(marker=None, limit=None, sort_field=None, sort_dir=None,
                   **kwargs):
    return api_base.entity_get_all(models.TimeLineEvent,
                                   marker=marker,
                                   limit=limit,
                                   sort_field=sort_field,
                                   sort_dir=sort_dir,
                                   **kwargs)


def events_get_count(**kwargs):
    return api_base.entity_get_count(models.TimeLineEvent,
                                     **kwargs)


def event_create(values):
    new_event = api_base.entity_create(models.TimeLineEvent, values)

    if CONF.enable_notifications:
        # Build the payload. Use of None is included to ensure that we don't
        # accidentally blow up the API call, but we don't anticipate it
        # happening.
        publish(author_id=request.current_user_id or None,
                method="POST",
                path=request.path or None,
                status=response.status_code or None,
                resource="timeline_events",
                resource_id=new_event.id or None)

    return new_event


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
