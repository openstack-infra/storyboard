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

ALL = (
    STORY_CREATED,
    STORY_DETAILS_CHANGED,
    USER_COMMENT,
    TASK_CREATED,
    TASK_ASSIGNEE_CHANGED,
    TASK_DETAILS_CHANGED,
    TASK_STATUS_CHANGED,
    TASK_PRIORITY_CHANGED,
    TASK_DELETED
)
