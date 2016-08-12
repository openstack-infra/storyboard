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

from storyboard.common import event_types
from storyboard.db.api import users as users_api


def story_created(event):
    return event


def story_details_changed(event):
    return event


def user_comment(event):
    return event


def task_created(event):
    return event


def task_status_changed(event):
    return event


def task_priority_changed(event):
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
    # NOTE: There is nothing to resolve, as the task title is already stored in
    # the info. There is no way to store an id because the task is hard deleted
    # at the moment we would query it.
    return event


def tags_added(event):
    return event


def tags_deleted(event):
    return event


def worklist_created(event):
    return event


def worklist_details_changed(event):
    return event


def worklist_permission_created(event):
    return event


def worklist_permissions_changed(event):
    return event


def worklist_filters_changed(event):
    return event


def worklist_contents_changed(event):
    return event


def board_created(event):
    return event


def board_details_changed(event):
    return event


def board_permission_created(event):
    return event


def board_permissions_changed(event):
    return event


def board_lanes_changed(event):
    return event


resolvers = {
    event_types.STORY_CREATED: story_created,
    event_types.STORY_DETAILS_CHANGED: story_details_changed,
    event_types.TAGS_ADDED: tags_added,
    event_types.TAGS_DELETED: tags_deleted,
    event_types.USER_COMMENT: user_comment,
    event_types.TASK_CREATED: task_created,
    event_types.TASK_DETAILS_CHANGED: task_details_changed,
    event_types.TASK_STATUS_CHANGED: task_status_changed,
    event_types.TASK_PRIORITY_CHANGED: task_priority_changed,
    event_types.TASK_ASSIGNEE_CHANGED: task_assignee_changed,
    event_types.TASK_DELETED: task_deleted,
    event_types.WORKLIST_CREATED: worklist_created,
    event_types.WORKLIST_DETAILS_CHANGED: worklist_details_changed,
    event_types.WORKLIST_PERMISSION_CREATED: worklist_permission_created,
    event_types.WORKLIST_PERMISSIONS_CHANGED: worklist_permissions_changed,
    event_types.WORKLIST_FILTERS_CHANGED: worklist_filters_changed,
    event_types.WORKLIST_CONTENTS_CHANGED: worklist_contents_changed,
    event_types.BOARD_CREATED: board_created,
    event_types.BOARD_DETAILS_CHANGED: board_details_changed,
    event_types.BOARD_PERMISSION_CREATED: board_permission_created,
    event_types.BOARD_PERMISSIONS_CHANGED: board_permissions_changed,
    event_types.BOARD_LANES_CHANGED: board_lanes_changed
}
