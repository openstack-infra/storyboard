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
from pecan import request
from pecan import response
from pecan import rest
from pecan.secure import secure
from wsme.exc import ClientSideError
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan

from storyboard.api.auth import authorization_checks as checks
from storyboard.api.v1 import base
from storyboard.db.api import comments as comments_api

CONF = cfg.CONF


class Comment(base.APIBase):
    """Any user may leave comments for stories. Also comments api is used by
    gerrit to leave service comments.
    """

    content = wtypes.text
    """The content of the comment."""

    action = wtypes.text
    """The action, that caused this comment to appear."""

    comment_type = wtypes.text
    """This type should serve as a hint for the web-client when rendering
    a comment."""

    is_active = bool
    """Is this an active comment, or has it been deleted?"""

    story_id = int
    """The ID of the corresponding Story."""

    author_id = int
    """The ID of User who has left the comment."""


class CommentsController(rest.RestController):
    """Manages comments."""

    @secure(checks.guest)
    @wsme_pecan.wsexpose(Comment, int, int)
    def get_one(self, story_id, comment_id):
        """Retrieve details about one comment.

        :param story_id: An ID of the story. It stays in params as a
        placeholder so that pecan knows where to match an incoming value.
        It will stay unused, as far as comments have their own unique ids.
        :param comment_id: An ID of the comment.
        """
        comment = comments_api.comment_get(comment_id)

        if comment:
            return Comment.from_db_model(comment)
        else:
            raise ClientSideError("Comment %s not found" % comment_id,
                                  status_code=404)

    @secure(checks.guest)
    @wsme_pecan.wsexpose([Comment], int, int, int)
    def get_all(self, story_id=None, marker=None, limit=None):
        """Retrieve all comments posted under specified story.

        :param story_id: filter comments by story ID.
        :param marker: The resource id where the page should begin.
        :param limit: The number of comments to retrieve.
        """

        # Boundary check on limit.
        if limit is None:
            limit = CONF.page_size_default
        limit = min(CONF.page_size_maximum, max(1, limit))

        # Resolve the marker record.
        marker_comment = comments_api.comment_get(marker)

        comment_count = comments_api.comment_get_count(story_id=story_id)
        comments = comments_api.comment_get_all(story_id=story_id,
                                                marker=marker_comment,
                                                limit=limit)

        # Apply the query response headers.
        response.headers['X-Limit'] = str(limit)
        response.headers['X-Total'] = str(comment_count)
        if marker_comment:
            response.headers['X-Marker'] = str(marker_comment.id)

        return [Comment.from_db_model(comment) for comment in comments]

    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(Comment, int, body=Comment)
    def post(self, story_id, comment):
        """Create a new comment.

        :param story_id: an id of a Story to add a Comment to.
        :param comment: The comment itself.
        """
        comment.story_id = story_id
        comment.author_id = request.current_user_id
        created_comment = comments_api.comment_create(comment.as_dict())
        return Comment.from_db_model(created_comment)

    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(Comment, int, int, body=Comment)
    def put(self, story_id, comment_id, comment_body):
        """Update an existing comment.

        :param story_id: a placeholder
        :param comment_id: the id of a Comment to be updated
        :param comment_body: an updated Comment
        """
        comment = comments_api.comment_get(comment_id)

        if request.current_user_id != comment.author_id:
            response.status_code = 400
            response.body = "You are not allowed to update this comment."
            return response

        updated_comment = comments_api.comment_update(comment_id,
                                                      comment_body.as_dict())

        return Comment.from_db_model(updated_comment)

    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(Comment, int, int)
    def delete(self, story_id, comment_id):
        """Update an existing comment.

        :param story_id: a placeholder
        :param comment_id: the id of a Comment to be updated
        """
        comment = comments_api.comment_get(comment_id)

        if request.current_user_id != comment.author_id:
            response.status_code = 400
            response.body = "You are not allowed to delete this comment."
            return response

        comments_api.comment_delete(comment_id)

        response.status_code = 204
        return response
