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

from datetime import datetime

from wsme import types as wtypes

from storyboard.api.v1 import base
from storyboard.common.custom_types import NameType
from storyboard.common import event_resolvers
from storyboard.common import event_types
from storyboard.db.api import comments as comments_api


class Comment(base.APIBase):
    """Any user may leave comments for stories. Also comments api is used by
    gerrit to leave service comments.
    """

    content = wtypes.text
    """The content of the comment."""

    is_active = bool
    """Is this an active comment, or has it been deleted?"""


class SystemInfo(base.APIBase):
    """Represents the system information for Storyboard
    """

    version = wtypes.text
    """The application version."""

    @classmethod
    def sample(cls):
        return cls(
            version="338c2d6")


class Project(base.APIBase):
    """The Storyboard Registry describes the open source world as ProjectGroups
    and Projects. Each ProjectGroup may be responsible for several Projects.
    For example, the OpenStack Infrastructure ProjectGroup has Zuul, Nodepool,
    Storyboard as Projects, among others.
    """

    name = NameType()
    """The Project unique name. This name will be displayed in the URL.
    At least 3 alphanumeric symbols. Minus and dot symbols are allowed as
    separators.
    """

    description = wtypes.text
    """Details about the project's work, highlights, goals, and how to
    contribute. Use plain text, paragraphs are preserved and URLs are
    linked in pages.
    """

    is_active = bool
    """Is this an active project, or has it been deleted?"""

    repo_url = wtypes.text
    """This is a repo link for this project"""

    autocreate_branches = bool
    """This flag means that storyboard will try to create task branches
    automatically from the branches declared in the code repository.
    """

    @classmethod
    def sample(cls):
        return cls(
            name="StoryBoard",
            description="This is an awesome project.",
            is_active=True,
            repo_url="git://git.openstack.org/openstack-infra/storyboard.git")


class ProjectGroup(base.APIBase):
    """Represents a group of projects."""

    name = NameType()
    """The Project Group unique name. This name will be displayed in the URL.
    At least 3 alphanumeric symbols. Minus and dot symbols are allowed as
    separators.
    """

    title = wtypes.text
    """The full name of the project group, which can contain spaces, special
    characters, etc.
    """

    @classmethod
    def sample(cls):
        return cls(
            name="Infra",
            title="Awesome projects")


class TaskStatusCount(base.APIBase):
    """Represents a task status and number of occurrences within a story."""
    key = wtypes.text
    count = int


class Story(base.APIBase):
    """The Story is the main element of StoryBoard. It represents a user story
    (generally a bugfix or a feature) that needs to be implemented. It will be
    broken down into a series of Tasks, which will each target a specific
    Project and branch.
    """

    title = wtypes.text
    """A descriptive label for the story, to show in listings."""

    description = wtypes.text
    """A complete description of the goal this story wants to cover."""

    is_bug = bool
    """Is this a bug or a feature :)"""

    creator_id = int
    """User ID of the Story creator"""

    story_type_id = int
    """ID of story type"""

    status = wtypes.text
    """The derived status of the story, one of 'active', 'merged', 'invalid'"""

    task_statuses = wtypes.ArrayType(TaskStatusCount)
    """The summary of each tasks/status."""

    tags = wtypes.ArrayType(wtypes.text)
    """Tag list assigned to this story."""

    @classmethod
    def sample(cls):
        return cls(
            title="Use Storyboard to manage Storyboard",
            description="We should use Storyboard to manage Storyboard.",
            is_bug=False,
            creator_id=1,
            task_statuses=[TaskStatusCount],
            story_type_id=1,
            status="active",
            tags=["t1", "t2"])


class Tag(base.APIBase):

    name = wtypes.text
    """The tag name"""

    @classmethod
    def sample(cls):
        return cls(name="low_hanging_fruit")


class Task(base.APIBase):
    """A Task represents an actionable work item, targeting a specific Project
    and a specific branch. It is part of a Story. There may be multiple tasks
    in a story, pointing to different projects or different branches. Each task
    is generally linked to a code change proposed in Gerrit.
    """

    title = wtypes.text
    """An optional short label for the task, to show in listings."""

    # TODO(ruhe): replace with enum
    status = wtypes.text
    """Status.
    Allowed values: ['todo', 'inprogress', 'invalid', 'review', 'merged'].
    Human readable versions are left to the UI.
    """

    creator_id = int
    """Id of the User who has created this Task"""

    story_id = int
    """The ID of the corresponding Story."""

    project_id = int
    """The ID of the corresponding Project."""

    assignee_id = int
    """The ID of the invidiual to whom this task is assigned."""

    priority = wtypes.text
    """The priority for this task, one of 'low', 'medium', 'high'"""

    branch_id = int
    """The ID of corresponding Branch"""

    milestone_id = int
    """The ID of corresponding Milestone"""


class Branch(base.APIBase):
    """Represents a branch."""

    name = wtypes.text
    """The branch unique name. This name will be displayed in the URL.
    At least 3 alphanumeric symbols.
    """

    project_id = int
    """The ID of the corresponding Project."""

    expired = bool
    """A binary flag that marks branches that should no longer be
    selectable in tasks."""

    expiration_date = datetime
    """Last date the expired flag was switched to True."""

    autocreated = bool
    """A flag that marks autocreated entries, so that they can
    be auto-expired when the corresponding branch is deleted in the git repo.
    """

    restricted = bool
    """This flag marks branch as restricted."""

    @classmethod
    def sample(cls):
        return cls(
            name="Storyboard-branch",
            project_id=1,
            expired=True,
            expiration_date=datetime(2015, 1, 1, 1, 1),
            autocreated=False,
            restricted=False
        )


class Milestone(base.APIBase):
    """Represents a milestone."""

    name = wtypes.text
    """The milestone unique name. This name will be displayed in the URL.
    At least 3 alphanumeric symbols.
    """

    branch_id = int
    """The ID of the corresponding Branch."""

    expired = bool
    """a binary flag that marks milestones that should no longer be
    selectable in completed tasks."""

    expiration_date = datetime
    """Last date the expired flag was switched to True."""

    @classmethod
    def sample(cls):
        return cls(
            name="Storyboard-milestone",
            branch_id=1,
            expired=True,
            expiration_date=datetime(2015, 1, 1, 1, 1)
        )


class Team(base.APIBase):
    """The Team is a group od Users with a fixed set of permissions.
    """

    name = NameType()
    """The Team unique name. This name will be displayed in the URL.
    At least 3 alphanumeric symbols. Minus and dot symbols are allowed as
    separators.
    """

    description = wtypes.text
    """Details about the team.
    """

    @classmethod
    def sample(cls):
        return cls(
            name="StoryBoard-core",
            description="Core reviewers of StoryBoard team.")


class TimeLineEvent(base.APIBase):
    """An event object should be created each time a story or a task state
    changes.
    """

    event_type = wtypes.text
    """This type should serve as a hint for the web-client when rendering
    a comment."""

    event_info = wtypes.text
    """A JSON encoded field with details about the event."""

    story_id = int
    """The ID of the corresponding Story."""

    author_id = int
    """The ID of User who has left the comment."""

    comment_id = int
    """The id of a comment linked to this event."""

    comment = Comment
    """The resolved comment."""

    @staticmethod
    def resolve_event_values(event):
        if event.comment_id:
            comment = comments_api.comment_get(event.comment_id)
            event.comment = Comment.from_db_model(comment)

        event = TimeLineEvent._resolve_info(event)

        return event

    @staticmethod
    def _resolve_info(event):
        if event.event_type == event_types.STORY_CREATED:
            return event_resolvers.story_created(event)

        elif event.event_type == event_types.STORY_DETAILS_CHANGED:
            return event_resolvers.story_details_changed(event)

        elif event.event_type == event_types.USER_COMMENT:
            return event_resolvers.user_comment(event)

        elif event.event_type == event_types.TASK_CREATED:
            return event_resolvers.task_created(event)

        elif event.event_type == event_types.TASK_STATUS_CHANGED:
            return event_resolvers.task_status_changed(event)

        elif event.event_type == event_types.TASK_PRIORITY_CHANGED:
            return event_resolvers.task_priority_changed(event)

        elif event.event_type == event_types.TASK_ASSIGNEE_CHANGED:
            return event_resolvers.task_assignee_changed(event)

        elif event.event_type == event_types.TASK_DETAILS_CHANGED:
            return event_resolvers.task_details_changed(event)

        elif event.event_type == event_types.TASK_DELETED:
            return event_resolvers.task_deleted(event)

        elif event.event_type == event_types.TAGS_ADDED:
            return event_resolvers.tags_added(event)

        elif event.event_type == event_types.TAGS_DELETED:
            return event_resolvers.tags_deleted(event)


class User(base.APIBase):
    """Represents a user."""

    full_name = wtypes.text
    """Full (Display) name."""

    openid = wtypes.text
    """The unique identifier, returned by an OpneId provider"""

    email = wtypes.text
    """Email Address."""

    # Todo(nkonovalov): use teams to define superusers
    is_superuser = bool

    last_login = datetime
    """Date of the last login."""

    enable_login = bool
    """Whether this user is permitted to log in."""

    @classmethod
    def sample(cls):
        return cls(
            full_name="Bart Simpson",
            openid="https://login.launchpad.net/+id/Abacaba",
            email="skinnerstinks@springfield.net",
            is_staff=False,
            is_active=True,
            is_superuser=True,
            last_login=datetime(2014, 1, 1, 16, 42))


class RefreshToken(base.APIBase):
    """Represents a user refresh token."""

    user_id = int
    """The ID of corresponding user."""

    refresh_token = wtypes.text
    """The refresh token."""

    expires_in = int
    """The number of seconds after creation when this token expires."""

    @classmethod
    def sample(cls):
        return cls(
            user_id=1,
            refresh_token="a_unique_refresh_token",
            expires_in=3600
        )


class AccessToken(base.APIBase):
    """Represents a user access token."""

    user_id = int
    """The ID of User to whom this token belongs."""

    access_token = wtypes.text
    """The access token."""

    expires_in = int
    """The number of seconds after creation when this token expires."""

    refresh_token = RefreshToken
    """The associated refresh token."""

    @classmethod
    def sample(cls):
        return cls(
            user_id=1,
            access_token="a_unique_access_token",
            expires_in=3600)


class TaskStatus(base.APIBase):
    key = wtypes.text
    name = wtypes.text


class Worklist(base.APIBase):
    """Represents a worklist."""

    title = wtypes.text
    """The title of the worklist."""

    creator_id = int
    """The ID of the User who created this worklist."""

    project_id = int
    """The ID of the Project this worklist is associated with."""

    permission_id = int
    """The ID of the Permission which defines who can edit this worklist."""

    private = bool
    """A flag to identify if this is a private or public worklist."""

    archived = bool
    """A flag to identify whether or not the worklist has been archived."""

    automatic = bool
    """A flag to identify whether the contents are obtained by a filter or are
    stored in the database."""


# NOTE(SotK): Criteria/Criterion is used as the existing code in the webclient
#             refers to such filters as Criteria.
class WorklistCriterion(base.APIBase):
    """Represents a filter used to construct an automatic worklist."""

    title = wtypes.text
    """The title of the filter, as displayed in the UI."""

    list_id = int
    """The ID of the Worklist this filter is for."""

    value = wtypes.text
    """The value to use as a filter."""

    field = wtypes.text
    """The field to filter by."""


class WorklistItem(base.APIBase):
    """Represents an item in a worklist.

    The item could be either a story or a task.

    """
    list_id = int
    """The ID of the Worklist this item belongs to."""

    item_id = int
    """The ID of the Task or Story for this item."""

    item_type = wtypes.text
    """The type of this item, either "story" or "task"."""

    list_position = int
    """The position of this item in the Worklist."""


class Lane(base.APIBase):
    """Represents a lane in a kanban board."""

    board_id = int
    """The ID of the board containing the lane."""

    list_id = int
    """The ID of the worklist which represents the lane."""

    position = int
    """The position of the lane in the board."""


class Board(base.APIBase):
    """Represents a kanban board made up of worklists."""

    title = wtypes.text
    """The title of the board."""

    description = wtypes.text
    """The description of the board."""

    creator_id = int
    """The ID of the User who created this board."""

    project_id = int
    """The ID of the Project this board is associated with."""

    permission_id = int
    """The ID of the Permission which defines who can edit this board."""

    private = bool
    """A flag to identify whether this is a private or public board."""

    archived = bool
    """A flag to identify whether or not the board has been archived."""

    lanes = wtypes.ArrayType(Lane)
    """A list containing the representions of the lanes in this board."""
