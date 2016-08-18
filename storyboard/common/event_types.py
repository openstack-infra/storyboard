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

"""
This module defines types for comment entries.
"""

STORY_CREATED = "story_created"
STORY_DETAILS_CHANGED = "story_details_changed"

TAGS_ADDED = "tags_added"
TAGS_DELETED = "tags_deleted"

USER_COMMENT = "user_comment"

TASK_CREATED = "task_created"
TASK_DETAILS_CHANGED = "task_details_changed"
TASK_STATUS_CHANGED = "task_status_changed"
TASK_PRIORITY_CHANGED = "task_priority_changed"
TASK_ASSIGNEE_CHANGED = "task_assignee_changed"
TASK_DELETED = "task_deleted"

WORKLIST_CREATED = "worklist_created"
# WORKLIST_DETAILS_CHANGED should occur when a value in any of the fields
# in the `worklists` database table is changed. Changes in related tables
# such as worklist_permissions, worklist_filters, and worklist_items have
# their own event types.
WORKLIST_DETAILS_CHANGED = "worklist_details_changed"
WORKLIST_PERMISSION_CREATED = "worklist_permission_created"
WORKLIST_PERMISSIONS_CHANGED = "worklist_permissions_changed"
WORKLIST_FILTERS_CHANGED = "worklist_filters_changed"
WORKLIST_CONTENTS_CHANGED = "worklist_contents_changed"

BOARD_CREATED = "board_created"
# BOARD_DETAILS_CHANGED should occur when a value in any of the fields
# in the `boards` database table is changed. Changes in related tables
# such as board_permissions, and board_worklists have their own event
# types.
BOARD_DETAILS_CHANGED = "board_details_changed"
BOARD_PERMISSION_CREATED = "board_permission_created"
BOARD_PERMISSIONS_CHANGED = "board_permissions_changed"
BOARD_LANES_CHANGED = "board_lanes_changed"

ALL = (
    STORY_CREATED,
    STORY_DETAILS_CHANGED,
    USER_COMMENT,
    TAGS_ADDED,
    TAGS_DELETED,
    TASK_CREATED,
    TASK_ASSIGNEE_CHANGED,
    TASK_DETAILS_CHANGED,
    TASK_STATUS_CHANGED,
    TASK_PRIORITY_CHANGED,
    TASK_DELETED,
    WORKLIST_CREATED,
    WORKLIST_DETAILS_CHANGED,
    WORKLIST_PERMISSION_CREATED,
    WORKLIST_PERMISSIONS_CHANGED,
    WORKLIST_FILTERS_CHANGED,
    WORKLIST_CONTENTS_CHANGED,
    BOARD_CREATED,
    BOARD_DETAILS_CHANGED,
    BOARD_PERMISSION_CREATED,
    BOARD_PERMISSIONS_CHANGED,
    BOARD_LANES_CHANGED
)
