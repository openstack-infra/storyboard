# Copyright (c) 2013 Mirantis Inc.
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

from oslo.config import cfg
from pecan import request
from pecan import response
from pecan import rest
from pecan.secure import secure
from wsme.exc import ClientSideError
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan

from storyboard.api.auth import authorization_checks as checks
from storyboard.api.v1 import base
from storyboard.api.v1.comments import CommentsController
from storyboard.db.api import stories as stories_api

CONF = cfg.CONF


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

    todo = int
    """The number of tasks remaining to be worked on."""

    inprogress = int
    """The number of in-progress tasks for this story."""

    review = int
    """The number of tasks in review for this story."""

    merged = int
    """The number of merged tasks for this story."""

    invalid = int
    """The number of invalid tasks for this story."""

    status = unicode
    """The derived status of the story, one of 'active', 'merged', 'invalid'"""

    @classmethod
    def sample(cls):
        return cls(
            title="Use Storyboard to manage Storyboard",
            description="We should use Storyboard to manage Storyboard.",
            is_bug=False,
            creator_id=1,
            todo=0,
            inprogress=1,
            review=1,
            merged=0,
            invalid=0,
            status="active")


class StoriesController(rest.RestController):
    """Manages operations on stories."""

    @secure(checks.guest)
    @wsme_pecan.wsexpose(Story, int)
    def get_one(self, story_id):
        """Retrieve details about one story.

        :param story_id: An ID of the story.
        """
        story = stories_api.story_get(story_id)

        if story:
            return Story.from_db_model(story)
        else:
            raise ClientSideError("Story %s not found" % id,
                                  status_code=404)

    @secure(checks.guest)
    @wsme_pecan.wsexpose([Story], int, int, int, unicode, unicode, unicode)
    def get_all(self, project_id=None, marker=None, limit=None,
                status=None, title=None, description=None):
        """Retrieve definitions of all of the stories.

        :param project_id: filter stories by project ID.
        :param marker: The resource id where the page should begin.
        :param limit: The number of stories to retrieve.
        :param status: Only show stories with this particular status.
        :param title: A string to filter the title by.
        :param description: A string to filter the description by.
        """

        # Boundary check on limit.
        if limit is None:
            limit = CONF.page_size_default
        limit = min(CONF.page_size_maximum, max(1, limit))

        # Resolve the marker record.
        marker_story = stories_api.story_get(marker)

        if marker_story is None or marker_story.project_id != project_id:
            marker_story = None

        stories = stories_api.story_get_all(marker=marker_story,
                                            limit=limit,
                                            project_id=project_id,
                                            status=status,
                                            title=title,
                                            description=description)
        story_count = stories_api.story_get_count(project_id=project_id,
                                                  status=status,
                                                  title=title,
                                                  description=description)

        # Apply the query response headers.
        response.headers['X-Limit'] = str(limit)
        response.headers['X-Total'] = str(story_count)
        if marker_story:
            response.headers['X-Marker'] = str(marker_story.id)

        return [Story.from_db_model(s) for s in stories]

    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(Story, body=Story)
    def post(self, story):
        """Create a new story.

        :param story: a story within the request body.
        """
        story_dict = story.as_dict()

        user_id = request.current_user_id
        story_dict.update({"creator_id": user_id})
        created_story = stories_api.story_create(story_dict)

        return Story.from_db_model(created_story)

    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(Story, int, body=Story)
    def put(self, story_id, story):
        """Modify this story.

        :param story_id: An ID of the story.
        :param story: a story within the request body.
        """
        updated_story = stories_api.story_update(
            story_id,
            story.as_dict(omit_unset=True))

        if updated_story:
            return Story.from_db_model(updated_story)
        else:
            raise ClientSideError("Story %s not found" % id,
                                  status_code=404)

    @secure(checks.superuser)
    @wsme_pecan.wsexpose(Story, int)
    def delete(self, story_id):
        """Delete this story.

        :param story_id: An ID of the story.
        """
        stories_api.story_delete(story_id)

        response.status_code = 204

    comments = CommentsController()
