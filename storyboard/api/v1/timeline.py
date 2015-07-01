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

from oslo_config import cfg
from pecan import abort
from pecan import request
from pecan import response
from pecan import rest
from pecan.secure import secure
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan

from storyboard.api.auth import authorization_checks as checks
from storyboard.api.v1.search import search_engine
from storyboard.api.v1 import wmodels
from storyboard.common import decorators
from storyboard.common import event_types
from storyboard.common import exception as exc
from storyboard.db.api import comments as comments_api
from storyboard.db.api import timeline_events as events_api
from storyboard.openstack.common.gettextutils import _  # noqa

CONF = cfg.CONF

SEARCH_ENGINE = search_engine.get_engine()


class TimeLineEventsController(rest.RestController):
    """Manages comments."""

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose(wmodels.TimeLineEvent, int, int)
    def get_one(self, story_id, event_id):
        """Retrieve details about one event.

        :param story_id: An ID of the story. It stays in params as a
                         placeholder so that pecan knows where to match an
                         incoming value. It will stay unused, as far as events
                         have their own unique ids.
        :param event_id: An ID of the event.
        """

        event = events_api.event_get(event_id)

        if event:
            wsme_event = wmodels.TimeLineEvent.from_db_model(event)
            wsme_event = wmodels.TimeLineEvent.resolve_event_values(wsme_event)
            return wsme_event
        else:
            raise exc.NotFound(_("Event %s not found") % event_id)

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose([wmodels.TimeLineEvent], int, [wtypes.text], int,
                        int, int, wtypes.text, wtypes.text)
    def get_all(self, story_id=None, event_type=None, marker=None,
                offset=None, limit=None, sort_field=None, sort_dir=None):
        """Retrieve all events that have happened under specified story.

        :param story_id: Filter events by story ID.
        :param event_type: A selection of event types to get.
        :param marker: The resource id where the page should begin.
        :param offset: The offset to start the page at.
        :param limit: The number of events to retrieve.
        :param sort_field: The name of the field to sort on.
        :param sort_dir: Sort direction for results (asc, desc).
        """

        # Boundary check on limit.
        if limit is not None:
            limit = max(0, limit)

        # Sanity check on event types.
        if event_type:
            for r_type in event_type:
                if r_type not in event_types.ALL:
                    msg = _('Invalid event_type requested. Event type must be '
                            'one of the following: %s')
                    msg = msg % (', '.join(event_types.ALL),)
                    abort(400, msg)

        # Resolve the marker record.
        marker_event = None
        if marker is not None:
            marker_event = events_api.event_get(marker)

        event_count = events_api.events_get_count(story_id=story_id,
                                                  event_type=event_type)
        events = events_api.events_get_all(story_id=story_id,
                                           event_type=event_type,
                                           marker=marker_event,
                                           offset=offset,
                                           limit=limit,
                                           sort_field=sort_field,
                                           sort_dir=sort_dir)

        # Apply the query response headers.
        if limit:
            response.headers['X-Limit'] = str(limit)
        response.headers['X-Total'] = str(event_count)
        if marker_event:
            response.headers['X-Marker'] = str(marker_event.id)
        if offset is not None:
            response.headers['X-Offset'] = str(offset)

        return [wmodels.TimeLineEvent.resolve_event_values(
            wmodels.TimeLineEvent.from_db_model(event)) for event in events]


class CommentsController(rest.RestController):
    """Manages comments."""

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose(wmodels.Comment, int, int)
    def get_one(self, story_id, comment_id):
        """Retrieve details about one comment.

        :param story_id: An ID of the story. It stays in params as a
                         placeholder so that pecan knows where to match an
                         incoming value. It will stay unused, as far as
                         comments have their own unique ids.
        :param comment_id: An ID of the comment.
        """

        comment = comments_api.comment_get(comment_id)

        if comment:
            return wmodels.Comment.from_db_model(comment)
        else:
            raise exc.NotFound(_("Comment %s not found") % comment_id)

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose([wmodels.Comment], int, int, int, wtypes.text,
                         wtypes.text)
    def get_all(self, story_id=None, marker=None, limit=None, sort_field='id',
                sort_dir='asc'):
        """Retrieve all comments posted under specified story.

        :param story_id: Filter comments by story ID.
        :param marker: The resource id where the page should begin.
        :param limit: The number of comments to retrieve.
        :param sort_field: The name of the field to sort on.
        :param sort_dir: Sort direction for results (asc, desc).
        """

        # Boundary check on limit.
        if limit is not None:
            limit = max(0, limit)

        # Resolve the marker record.
        marker_event = None
        if marker:
            event_query = \
                events_api.events_get_all(comment_id=marker,
                                          event_type=event_types.USER_COMMENT)
            if len(event_query) > 0:
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
        if limit:
            response.headers['X-Limit'] = str(limit)
        response.headers['X-Total'] = str(events_count)
        if marker_event:
            response.headers['X-Marker'] = str(marker)

        return [wmodels.Comment.from_db_model(comment) for comment in comments]

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wmodels.TimeLineEvent, int, body=wmodels.Comment)
    def post(self, story_id, comment):
        """Create a new comment.

        :param story_id: An id of a Story to add a Comment to.
        :param comment: The comment itself.
        """

        created_comment = comments_api.comment_create(comment.as_dict())

        event_values = {
            "story_id": story_id,
            "author_id": request.current_user_id,
            "event_type": event_types.USER_COMMENT,
            "comment_id": created_comment.id
        }
        event = wmodels.TimeLineEvent.from_db_model(
            events_api.event_create(event_values))
        event = wmodels.TimeLineEvent.resolve_event_values(event)
        return event

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wmodels.Comment, int, int, body=wmodels.Comment)
    def put(self, story_id, comment_id, comment_body):
        """Update an existing comment.

        :param story_id: A placeholder.
        :param comment_id: The id of a Comment to be updated.
        :param comment_body: An updated Comment.
        """

        comments_api.comment_get(comment_id)
        comment_author_id = events_api.events_get_all(
            comment_id=comment_id)[0].author_id
        if request.current_user_id != comment_author_id:
            abort(403, _("You are not allowed to update this comment."))

        updated_comment = comments_api.comment_update(comment_id,
                                                      comment_body.as_dict(
                                                          omit_unset=True
                                                      ))

        return wmodels.Comment.from_db_model(updated_comment)

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wmodels.Comment, int, int, status_code=204)
    def delete(self, story_id, comment_id):
        """Update an existing comment.

        :param story_id: A placeholder.
        :param comment_id: The id of a Comment to be updated.
        """

        comment = comments_api.comment_get(comment_id)

        if request.current_user_id != comment.author_id:
            abort(403, _("You are not allowed to delete this comment."))

        comments_api.comment_delete(comment_id)

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose([wmodels.Comment], wtypes.text, wtypes.text, int,
                         int)
    def search(self, q="", marker=None, limit=None):
        """The search endpoint for comments.

        :param q: The query string.
        :return: List of Comments matching the query.
        """

        comments = SEARCH_ENGINE.comments_query(q=q,
                                                marker=marker,
                                                limit=limit)

        return [wmodels.Comment.from_db_model(comment) for comment in comments]
