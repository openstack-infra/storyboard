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

from oslo_config import cfg
from pecan import request
from pecan import rest
from pecan.secure import secure
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan

from storyboard._i18n import _
from storyboard.api.auth import authorization_checks as checks
from storyboard.api.v1 import wmodels
from storyboard.common import exception as exc
from storyboard.db.api import stories as stories_api
from storyboard.db.api import story_tags as tags_api
from storyboard.db.api import timeline_events as events_api

CONF = cfg.CONF


class TagsController(rest.RestController):
    """Manages tags."""

    @secure(checks.guest)
    @wsme_pecan.wsexpose(wmodels.Tag, int)
    def get_one(self, tag_id):
        """Retrieve details about one tag.

        Example::

          curl https://my.example.org/api/v1/tags/159

        :param tag_id: An ID of the tag.
        """
        tag = tags_api.tag_get_by_id(tag_id)

        if tag:
            tag_model = wmodels.Tag.from_db_model(tag)
            tag_model.set_popularity(tag)
            return tag_model
        else:
            raise exc.NotFound(_("Tag %s not found") % tag_id)

    @secure(checks.guest)
    @wsme_pecan.wsexpose([wmodels.Tag], int, wtypes.text, int, int, int)
    def get_all(self, story_id=None, name=None, marker=None, limit=None,
                offset=None):
        """Retrieve all tags.

        Example::

          curl https://my.example.org/api/v1/tags

        :param story_id: Filter tags by story ID.
        :param name: Filter tags by name.
        :param marker: ID of the tag to start results from.
        :param limit: Maximum number of results per page.
        :param offset: Number of results to offset page by.
        """

        if not story_id:
            marker_tag = tags_api.tag_get_by_id(marker)
            tags = tags_api.tag_get_all(name=name,
                                        marker=marker_tag,
                                        limit=limit,
                                        offset=offset)

            result = []
            for t in tags:
                tag = wmodels.Tag.from_db_model(t)
                tag.set_popularity(t)
                result.append(tag)
            return result

        story = stories_api.story_get(
            story_id, current_user=request.current_user_id)
        if not story:
            raise exc.NotFound("Story %s not found" % story_id)

        result = []
        for t in story.tags:
            tag = wmodels.Tag.from_db_model(t)
            tag.set_popularity(t)
            result.append(tag)
        return result

    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wmodels.Story, int, body=[wtypes.text])
    def put(self, story_id, tags=[], body=[]):
        """Add a list of tags to a Story.

        Example::

          curl https://my.example.org/api/v1/tags/19 -X PUT \\
          -H 'Authorization: Bearer MY_ACCESS_TOKEN' \\
          -H 'Content-Type: application/json;charset=UTF-8' \\
          --data-binary '["taga","tagb"]'

        :param story_id: An id of a Story to which the tags should be added.
        :param tags: A list of tags to be added.
        """
        tags = (tags or []) + (body or [])

        story = stories_api.story_get(
            story_id, current_user=request.current_user_id)
        if not story:
            raise exc.NotFound("Story %s not found" % story_id)

        for tag in tags:
            stories_api.story_add_tag(
                story_id, tag, current_user=request.current_user_id)
        # For some reason the story gets cached and the tags do not appear.
        stories_api.api_base.get_session().expunge(story)

        story = stories_api.story_get(
            story_id, current_user=request.current_user_id)
        events_api.tags_added_event(story_id=story_id,
                                    author_id=request.current_user_id,
                                    story_title=story.title,
                                    tags=tags)
        return wmodels.Story.from_db_model(story)

    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wmodels.Tag, wtypes.text)
    def post(self, tag_name):
        """Create a tag not attached to any Story.

        Example::

           curl https://my.example.org/api/v1/tags \\
           -H 'Authorization: Bearer MY_ACCESS_TOKEN' \\
           -H 'Content-Type: application/json;charset=UTF-8' \\
           --data-binary '{"tag_name":"created-via-api"}'

        :param tag_name: The name of a new tag.
        """

        tag = tags_api.tag_create({"name": tag_name})
        return wmodels.Tag.from_db_model(tag)

    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(None, int, body=[wtypes.text], status_code=204)
    def delete(self, story_id, tags):
        """Remove a list of tags from a Story.

        Example::

          curl https://my.example.org/api/v1/tags/19 -X DELETE \\
          -H 'Authorization: Bearer MY_ACCESS_TOKEN' \\
          -H 'Content-Type: application/json;charset=UTF-8' \\
          --data-binary '["taga","tagb"]'

        :param story_id: An id of a Story from which the tags should be
                         removed.
        :param tags: A list of tags to be removed.
        """

        story = stories_api.story_get(
            story_id, current_user=request.current_user_id)
        if not story:
            raise exc.NotFound("Story %s not found" % story_id)

        for tag in tags:
            stories_api.story_remove_tag(
                story_id, tag, current_user=request.current_user_id)

        events_api.tags_deleted_event(story_id=story_id,
                                      author_id=request.current_user_id,
                                      story_title=story.title,
                                      tags=tags)
