# Copyright (c) 2013 Hewlett-Packard Development Company, L.P.
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

from storyboard._i18n import _
from storyboard.api.auth import authorization_checks as checks
from storyboard.api.v1 import base
from storyboard.common import decorators
from storyboard.db.api import subscription_events as subscription_events_api
from storyboard.db.api import users as user_api


CONF = cfg.CONF


class SubscriptionEvent(base.APIBase):
    """A model that describes a resource subscription.
    """

    subscriber_id = int
    """The owner of this subscription.
    """

    author_id = int
    """The author who triggered this event.
    """

    event_type = wtypes.text
    """This type should serve as a hint for the web-client when rendering
    a comment."""

    event_info = wtypes.text
    """A JSON encoded field with details about the event."""

    @classmethod
    def sample(cls):
        return cls(
            subscriber_id=1,
            author_id=1,
            event_type="project",
            event_info={"task_title": "story1", "old_status": "todo",
                        "task_id": 38, "new_status": "inprogress"}
        )


class SubscriptionEventsController(rest.RestController):
    """REST controller for Subscriptions.

    Provides Create, Delete, and search methods for resource
    subscriptionEvents.
    """

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(SubscriptionEvent, int)
    def get_one(self, subscription_event_id):
        """Retrieve a specific subscription record.

        :param subscription_event_id: The unique id of this subscription.
        """
        subscription_event = subscription_events_api \
            .subscription_events_get(subscription_event_id)

        current_user = user_api.user_get(request.current_user_id)
        if current_user.id != subscription_event.subscriber_id and \
                not current_user.is_superuser:
            abort(403, _("Permission Denied"))

        return SubscriptionEvent.from_db_model(subscription_event)

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose([SubscriptionEvent], int, int, int, wtypes.text,
                         int, wtypes.text, wtypes.text)
    def get(self, marker=None, offset=None, limit=None, event_type=None,
            subscriber_id=None, sort_field='id', sort_dir='asc'):
        """Retrieve a list of subscriptions.

        :param marker: The resource id where the page should begin.
        :param offset: The offset to begin the page at.
        :param limit: The number of subscriptions to retrieve.
        :param event_type: The type of resource to search by.
        :param subscriber_id: The unique ID of the subscriber to search by.
        :param sort_field: The name of the field to sort on.
        :param sort_dir: Sort direction for results (asc, desc).
        """

        # Boundary check on limit.
        if limit is not None:
            limit = max(0, limit)

        # Resolve the marker record.
        marker_sub = subscription_events_api.subscription_events_get(marker)
        current_user = user_api.user_get(request.current_user_id)
        if current_user.id != subscriber_id and \
                not current_user.is_superuser:
            abort(403, _("Permission Denied"))

        if marker_sub and marker_sub.user_id != subscriber_id:
            marker_sub = None

        subscriptions = subscription_events_api.subscription_events_get_all(
            marker=marker_sub,
            offset=offset,
            limit=limit,
            subscriber_id=subscriber_id,
            event_type=event_type,
            sort_field=sort_field,
            sort_dir=sort_dir)
        subscription_count = \
            subscription_events_api.subscription_events_get_count(
                subscriber_id=subscriber_id,
                event_type=event_type)

        # Apply the query response headers.
        if limit:
            response.headers['X-Limit'] = str(limit)
        if offset is not None:
            response.headers['X-Offset'] = str(offset)
        response.headers['X-Total'] = str(subscription_count)
        if marker_sub:
            response.headers['X-Marker'] = str(marker_sub.id)

        return [SubscriptionEvent.from_db_model(s) for s in subscriptions]

    @decorators.db_exceptions
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(None, int, status_code=204)
    def delete(self, subscription_event_id):
        """Delete a specific subscription.

        :param subscription_event_id: The unique id of the
                                      subscription_event to delete.
        """
        subscription_event = subscription_events_api \
            .subscription_events_get(subscription_event_id)

        current_user = user_api.user_get(request.current_user_id)
        if current_user.id != subscription_event.subscriber_id and \
                not current_user.is_superuser:
            abort(403, _("Permission Denied"))

        subscription_events_api.subscription_events_delete(
            subscription_event_id)
