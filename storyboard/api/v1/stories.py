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

from pecan import rest
from wsme.exc import ClientSideError
import wsmeext.pecan as wsme_pecan

import storyboard.api.v1.wsme_models as wsme_models


class StoriesController(rest.RestController):
    """Manages operations on stories."""

    _custom_actions = {
        "add_task": ["POST"],
        "add_comment": ["POST"]
    }

    @wsme_pecan.wsexpose(wsme_models.Story, unicode)
    def get_one(self, id):
        """Retrieve details about one story.

        :param id: An ID of the story.
        """
        story = wsme_models.Story.get(id=id)
        if not story:
            raise ClientSideError("Story %s not found" % id,
                                  status_code=404)
        return story

    @wsme_pecan.wsexpose([wsme_models.Story])
    def get(self):
        """Retrieve definitions of all of the stories."""
        stories = wsme_models.Story.get_all()
        return stories

    @wsme_pecan.wsexpose(wsme_models.Story, wsme_models.Story)
    def post(self, story):
        """Create a new story.

        :param story: a story within the request body.
        """
        created_story = wsme_models.Story.create(wsme_entry=story)
        if not created_story:
            raise ClientSideError("Could not create a story")
        return created_story

    @wsme_pecan.wsexpose(wsme_models.Story, unicode, wsme_models.Story)
    def put(self, story_id, story):
        """Modify this story.

        :param story_id: An ID of the story.
        :param story: a story within the request body.
        """
        updated_story = wsme_models.Story.update("id", story_id, story)
        if not updated_story:
            raise ClientSideError("Could not update story %s" % story_id)
        return updated_story

    @wsme_pecan.wsexpose(wsme_models.Story, unicode, wsme_models.Task)
    def add_task(self, story_id, task):
        """Associate a task with a story.

        :param story_id: An ID of the story.
        :param task: a task within the request body.
        """
        updated_story = wsme_models.Story.add_task(story_id, task)
        if not updated_story:
            raise ClientSideError("Could not add task to story %s" % story_id)
        return updated_story

    @wsme_pecan.wsexpose(wsme_models.Story, unicode, wsme_models.Comment)
    def add_comment(self, story_id, comment):
        """Add a comment with a story.

        :param story_id: An ID of the story.
        :param comment: a comment within the request body.
        """
        updated_story = wsme_models.Story.add_comment(story_id, comment)
        if not updated_story:
            raise ClientSideError("Could not add comment to story %s"
                                  % story_id)
        return updated_story
