# Copyright (c) 2014 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json

from storyboard.db.api import users as users_api


def story_created(event):
    return event


def story_story_details_changed(event):
    return event


def user_comment(event):
    return event


def task_created(event):
    return event


def task_status_changed(event):
    return event


def task_assignee_changed(event):
    event_info = json.loads(event.event_info)

    old_assignee_id = event_info["old_assignee_id"]
    old_assignee = users_api.user_get(old_assignee_id)
    if old_assignee:
        old_fullname = old_assignee.full_name
    else:
        old_fullname = "unassigned"
    event_info["old_assignee_fullname"] = old_fullname

    new_assignee_id = event_info["new_assignee_id"]
    new_assignee = users_api.user_get(new_assignee_id)
    if new_assignee:
        new_fullname = new_assignee.full_name
    else:
        new_fullname = "unassigned"
    event_info["new_assignee_fullname"] = new_fullname

    event.event_info = json.dumps(event_info)
    return event


def task_details_changed(event):
    return event


def task_deleted(event):
    #NOTE: There is nothing to resolve, as the task title is already stored in
    # the info. There is no way to store an id because the task is hard deleted
    # at the moment we would query it.
    return event
