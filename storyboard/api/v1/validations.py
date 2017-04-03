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

from storyboard.db.models import CommonLength


USERS_PUT_SCHEMA = {
    "name": "user_schema",
    "type": "object",
    "properties": {
        "full_name": {
            "type": ["string"],
            "minLength": CommonLength.lower_middle_length,
            "maxLength": CommonLength.top_large_length
        },
        "email": {
            "type": ["string"],
            "minLength": CommonLength.lower_large_length,
            "maxLength": CommonLength.top_large_length
        },
        "openid": {
            "type": ["string", "null"],
            "maxLength": CommonLength.top_large_length
        }
    }
}

USERS_POST_SCHEMA = copy.deepcopy(USERS_PUT_SCHEMA)
USERS_POST_SCHEMA["required"] = ["full_name", "email"]

USER_PREFERENCES_POST_SCHEMA = {
    "name": "userPreference_schema",
    "type": "object",
    "patternProperties": {
        "^.{3,100}$": {
            "type": ["string", "boolean", "number", "null"],
            "minLength": CommonLength.lower_short_length,
            "maxLength": CommonLength.top_large_length
        }
    },
    "additionalProperties": False
}

TEAMS_PUT_SCHEMA = {
    "name": "team_schema",
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "minLength": CommonLength.lower_middle_length,
            "maxLength": CommonLength.top_large_length
        }
    }
}

TEAMS_POST_SCHEMA = copy.deepcopy(TEAMS_PUT_SCHEMA)
TEAMS_POST_SCHEMA["required"] = ["name"]

"""permission_chema is not applied anywhere until permission controller
is implemented"""

PERMISSIONS_PUT_SCHEMA = {
    "name": "permission_schema",
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "minLength": CommonLength.lower_middle_length,
            "maxLength": CommonLength.top_short_length
        },
        "codename": {
            "type": "string",
            "maxLength": CommonLength.top_large_length
        }
    }
}

PERMISSIONS_POST_SCHEMA = copy.deepcopy(PERMISSIONS_PUT_SCHEMA)
PERMISSIONS_POST_SCHEMA["required"] = ["name", "codename"]

PROJECTS_PUT_SCHEMA = {
    "name": "project_schema",
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "minLength": CommonLength.lower_middle_length,
            "maxLength": CommonLength.top_middle_length
        },
        "repo_url": {
            "type": ["string", "null"],
            "maxLength": CommonLength.top_large_length
        }
    }
}

PROJECTS_POST_SCHEMA = copy.deepcopy(PROJECTS_PUT_SCHEMA)
PROJECTS_POST_SCHEMA["required"] = ["name"]

PROJECT_GROUPS_PUT_SCHEMA = {
    "name": "projectGroup_schema",
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "minLength": CommonLength.lower_middle_length,
            "maxLength": CommonLength.top_middle_length
        },
        "title": {
            "type": "string",
            "minLength": CommonLength.lower_middle_length,
            "maxLength": CommonLength.top_large_length
        }
    }
}

PROJECT_GROUPS_POST_SCHEMA = copy.deepcopy(PROJECT_GROUPS_PUT_SCHEMA)
PROJECT_GROUPS_POST_SCHEMA["required"] = ["name", "title"]

STORIES_PUT_SCHEMA = {
    "name": "story_schema",
    "type": "object",
    "properties": {
        "title": {
            "type": "string",
            "minLength": CommonLength.lower_large_length,
            "maxLength": CommonLength.top_large_length,
        }
    }
}

STORIES_POST_SCHEMA = copy.deepcopy(STORIES_PUT_SCHEMA)
STORIES_POST_SCHEMA["required"] = ["title"]

TASKS_PUT_SCHEMA = {
    "name": "task_schema",
    "type": "object",
    "properties": {
        "title": {
            "type": "string",
            "minLength": CommonLength.lower_middle_length,
            "maxLength": CommonLength.top_large_length
        }
    }
}

TASKS_POST_SCHEMA = copy.deepcopy(TASKS_PUT_SCHEMA)
TASKS_POST_SCHEMA["required"] = ["title"]

BRANCHES_PUT_SCHEMA = {
    "name": "branch_schema",
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "minLength": CommonLength.lower_middle_length,
            "maxLength": CommonLength.top_middle_length
        }
    }
}

BRANCHES_POST_SCHEMA = copy.deepcopy(BRANCHES_PUT_SCHEMA)
BRANCHES_POST_SCHEMA["required"] = ["name"]

MILESTONES_PUT_SCHEMA = {
    "name": "milestone_schema",
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "minLength": CommonLength.lower_middle_length,
            "maxLength": CommonLength.top_middle_length
        }
    }
}

MILESTONES_POST_SCHEMA = copy.deepcopy(MILESTONES_PUT_SCHEMA)
MILESTONES_POST_SCHEMA["required"] = ["name"]

STORY_TAGS_PUT_SCHEMA = {
    "name": "storyTag_schema",
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "minLength": CommonLength.lower_middle_length,
            "maxLength": CommonLength.top_short_length
        }
    }
}

STORY_TAGS_POST_SCHEMA = copy.deepcopy(STORY_TAGS_PUT_SCHEMA)
STORY_TAGS_POST_SCHEMA["required"] = ["name"]
