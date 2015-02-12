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

from oslo.config import cfg
from pecan import rest
from pecan.secure import secure
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan

from storyboard.api.auth import authorization_checks as checks
from storyboard.api.v1 import wmodels
from storyboard.common import exception as exc
from storyboard.db.api import stories as stories_api
from storyboard.db.api import story_tags as tags_api
from storyboard.openstack.common.gettextutils import _  # noqa

CONF = cfg.CONF


class TagsController(rest.RestController):
    """Manages tags."""

    _custom_actions = {"search": ["GET"]}

    @secure(checks.guest)
    @wsme_pecan.wsexpose(wmodels.Tag, int)
    def get_one(self, tag_id):
        """Retrieve details about one tag.

        :param tag_id: An ID of the tag.
        """
        tag = tags_api.tag_get_by_id(tag_id)

        if tag:
            return wmodels.Tag.from_db_model(tag)
        else:
            raise exc.NotFound(_("Tag %s not found") % tag_id)

    @secure(checks.guest)
    @wsme_pecan.wsexpose([wmodels.Tag], int, int, int)
    def get_all(self, story_id=None, marker=None, limit=None):
        """Retrieve all tags for a given Story. If no story_id is provided
        all tags will be returned.

        :param story_id: filter tags by story ID.
        """

        if not story_id:
            marker_tag = tags_api.tag_get_by_id(marker)
            tags = tags_api.tag_get_all(marker_tag, limit)

            return [wmodels.Tag.from_db_model(t) for t in tags]

        story = stories_api.story_get(story_id)
        if not story:
            raise exc.NotFound("Story %s not found" % story_id)

        return [wmodels.Tag.from_db_model(t) for t in story.tags]

    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wmodels.Story, int, body=[wtypes.text])
    def put(self, story_id, tags):
        """Add a list of tags to a Story.

        :param story_id: an id of a Story to which the tags should be added.
        :param tags: a list of tags to be added
        """

        story = stories_api.story_get(story_id)
        if not story:
            raise exc.NotFound("Story %s not found" % story_id)

        for tag in tags:
            stories_api.story_add_tag(story_id, tag)

        story = stories_api.story_get(story_id)
        return wmodels.Story.from_db_model(story)

    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wmodels.Tag, wtypes.text)
    def post(self, tag_name):
        """Create a tag not attached to any Story.

        :param tag_name: The name of a new tag
        :return: the tag
        """

        tag = tags_api.tag_create({"name": tag_name})
        return wmodels.Tag.from_db_model(tag)

    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(None, int, body=[wtypes.text], status_code=204)
    def delete(self, story_id, tags):
        """Remove a list of tags from a Story.

        :param story_id: an id of a Story from which the tags should be
        removed.
        :param tags: a list of tags to be removed
        """

        story = stories_api.story_get(story_id)
        if not story:
            raise exc.NotFound("Story %s not found" % story_id)

        for tag in tags:
            stories_api.story_remove_tag(story_id, tag)
