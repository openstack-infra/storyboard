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
from storyboard.api.v1.search import search_engine
from storyboard.common import event_resolvers
from storyboard.common import event_types
from storyboard.db.api import comments as comments_api
from storyboard.db.api import timeline_events as events_api

CONF = cfg.CONF

SEARCH_ENGINE = search_engine.get_engine()


class Comment(base.APIBase):
    """Any user may leave comments for stories. Also comments api is used by
    gerrit to leave service comments.
    """

    content = wtypes.text
    """The content of the comment."""

    is_active = bool
    """Is this an active comment, or has it been deleted?"""


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


class TimeLineEventsController(rest.RestController):
    """Manages comments."""

    @secure(checks.guest)
    @wsme_pecan.wsexpose(TimeLineEvent, int, int)
    def get_one(self, story_id, event_id):
        """Retrieve details about one event.

        :param story_id: An ID of the story. It stays in params as a
        placeholder so that pecan knows where to match an incoming value.
        It will stay unused, as far as events have their own unique ids.
        :param event_id: An ID of the event.
        """
        event = events_api.event_get(event_id)

        if event:
            wsme_event = TimeLineEvent.from_db_model(event)
            wsme_event = TimeLineEvent.resolve_event_values(wsme_event)
            return wsme_event
        else:
            raise ClientSideError("Comment %s not found" % event_id,
                                  status_code=404)

    @secure(checks.guest)
    @wsme_pecan.wsexpose([TimeLineEvent], int, int, int, unicode, unicode)
    def get_all(self, story_id=None, marker=None, limit=None, sort_field=None,
                sort_dir=None):
        """Retrieve all events that have happened under specified story.

        :param story_id: filter events by story ID.
        :param marker: The resource id where the page should begin.
        :param limit: The number of events to retrieve.
        :param sort_field: The name of the field to sort on.
        :param sort_dir: sort direction for results (asc, desc).
        """

        # Boundary check on limit.
        if limit is None:
            limit = CONF.page_size_default
        limit = min(CONF.page_size_maximum, max(1, limit))

        # Resolve the marker record.
        marker_event = events_api.event_get(marker)

        event_count = events_api.events_get_count(story_id=story_id)
        events = events_api.events_get_all(story_id=story_id,
                                           marker=marker_event,
                                           limit=limit,
                                           sort_field=sort_field,
                                           sort_dir=sort_dir)

        # Apply the query response headers.
        response.headers['X-Limit'] = str(limit)
        response.headers['X-Total'] = str(event_count)
        if marker_event:
            response.headers['X-Marker'] = str(marker_event.id)

        return [TimeLineEvent.resolve_event_values(
            TimeLineEvent.from_db_model(event)) for event in events]


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
    @wsme_pecan.wsexpose([Comment], int, int, int, unicode, unicode)
    def get_all(self, story_id=None, marker=None, limit=None, sort_field='id',
                sort_dir='asc'):
        """Retrieve all comments posted under specified story.

        :param story_id: filter comments by story ID.
        :param marker: The resource id where the page should begin.
        :param limit: The number of comments to retrieve.
        :param sort_field: The name of the field to sort on.
        :param sort_dir: sort direction for results (asc, desc).
        """

        # Boundary check on limit.
        if limit is None:
            limit = CONF.page_size_default
        limit = min(CONF.page_size_maximum, max(1, limit))

        # Resolve the marker record.
        event_query = events_api.events_get_all(comment_id=marker)
        if len(event_query) == 0:
            raise ClientSideError("Marker comment %s not found" % marker,
                                  status_code=404)

        marker_event = event_query[0]
        events_count = events_api.events_get_count(
            story_id=story_id,
            event_type=event_types.USER_COMMENT)

        events = events_api.events_get_all(story_id=story_id,
                                           marker=marker_event,
                                           limit=limit,
                                           event_type=event_types.USER_COMMENT,
                                           sort_field=sort_field,
                                           sort_dir=sort_dir)

        comments = [comments_api.comment_get(event.comment_id)
                    for event in events]

        # Apply the query response headers.
        response.headers['X-Limit'] = str(limit)
        response.headers['X-Total'] = str(events_count)
        if marker_event:
            response.headers['X-Marker'] = str(marker)

        return [Comment.from_db_model(comment) for comment in comments]

    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(TimeLineEvent, int, body=Comment)
    def post(self, story_id, comment):
        """Create a new comment.

        :param story_id: an id of a Story to add a Comment to.
        :param comment: The comment itself.
        """

        created_comment = comments_api.comment_create(comment.as_dict())

        event_values = {
            "story_id": story_id,
            "author_id": request.current_user_id,
            "event_type": event_types.USER_COMMENT,
            "comment_id": created_comment.id
        }
        event = TimeLineEvent.from_db_model(
            events_api.event_create(event_values))
        event = TimeLineEvent.resolve_event_values(event)
        return event

    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(Comment, int, int, body=Comment)
    def put(self, story_id, comment_id, comment_body):
        """Update an existing comment.

        :param story_id: a placeholder
        :param comment_id: the id of a Comment to be updated
        :param comment_body: an updated Comment
        """
        comments_api.comment_get(comment_id)
        comment_author_id = events_api.events_get_all(
            comment_id=comment_id)[0].author_id
        if request.current_user_id != comment_author_id:
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

    @secure(checks.guest)
    @wsme_pecan.wsexpose([Comment], unicode, unicode, int, int)
    def search(self, q="", marker=None, limit=None):
        """The search endpoint for comments.

        :param q: The query string.
        :return: List of Comments matching the query.
        """

        comments = SEARCH_ENGINE.comments_query(q=q,
                                                marker=marker,
                                                limit=limit)

        return [Comment.from_db_model(comment) for comment in comments]
