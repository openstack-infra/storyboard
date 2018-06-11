# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
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

import json

from oslo_config import cfg
from oslo_log import log
from pika.exceptions import ConnectionClosed

from storyboard.notifications.conf import NOTIFICATION_OPTS
from storyboard.notifications.connection_service import ConnectionService
from storyboard._i18n import _, _LW, _LE


CONF = cfg.CONF
LOG = log.getLogger(__name__)
PUBLISHER = None


class Publisher(ConnectionService):
    """A generic message publisher that uses delivery confirmation to ensure
    that messages are delivered, and will keep a running cache of unsent
    messages while the publisher is attempting to reconnect.
    """

    def __init__(self, conf):
        """Setup the publisher instance based on our configuration.

        :param conf A configuration object.
        """
        super(Publisher, self).__init__(conf)

        self._pending = list()

        self.add_open_hook(self._publish_pending)

    def _publish_pending(self):
        """Publishes any pending messages that were broadcast while the
        publisher was connecting.
        """

        # Shallow copy, so we can iterate over it without having it be modified
        # out of band.
        pending = list(self._pending)

        for payload in pending:
            self._publish(payload)

    def _publish(self, payload):
        """Publishes a payload to the passed exchange. If it encounters a
        failure, will store the payload for later.

        :param Payload payload: The payload to send.
        """
        LOG.debug(_("Sending message to %(name)s [%(topic)s]") %
                  {'name': self._exchange_name, 'topic': payload.topic})

        # First check, are we closing?
        if self._closing:
            LOG.warning(_LW("Cannot send message, publisher is closing."))
            if payload not in self._pending:
                self._pending.append(payload)
            return

        # Second check, are we open?
        if not self._open:
            LOG.debug(_("Cannot send message, publisher is connecting."))
            if payload not in self._pending:
                self._pending.append(payload)
            self._reconnect()
            return

        # Third check, are we in a sane state? This should never happen,
        # but just in case...
        if not self._connection or not self._channel:
            LOG.error(_LE("Cannot send message, publisher is "
                          "an unexpected state."))
            if payload not in self._pending:
                self._pending.append(payload)
            self._reconnect()
            return

        # Try to send a message. If we fail, schedule a reconnect and store
        # the message.
        try:
            self._channel.basic_publish(self._exchange_name,
                                        payload.topic,
                                        json.dumps(payload.payload,
                                                   ensure_ascii=False),
                                        self._properties)
            if payload in self._pending:
                self._pending.remove(payload)
            return True
        except (ConnectionClosed, AttributeError) as cc:
            LOG.warning(_LW("Attempted to send message on closed connection."))
            LOG.debug(cc)
            self._open = False
            if payload not in self._pending:
                self._pending.append(payload)
            self._reconnect()
            return False

    def publish_message(self, topic, payload):
        """Publishes a message to RabbitMQ.
        """
        self._publish(Payload(topic, payload))


class Payload(object):
    def __init__(self, topic, payload):
        """Setup the example publisher object, passing in the URL we will use
        to connect to RabbitMQ.

        :param topic string The exchange topic to broadcast on.
        :param payload string The message payload to send.
        """

        self.topic = topic
        self.payload = payload


def publish(resource, author_id=None, method=None, url=None, path=None,
            query_string=None, status=None, resource_id=None,
            sub_resource=None, sub_resource_id=None, resource_before=None,
            resource_after=None):
    """Send a message for an API event to the storyboard exchange. The message
    will be automatically JSON encoded.

    :param resource: The extrapolated resource type (project, story, etc).
    :param author_id: The ID of the author who performed this action.
    :param method: The HTTP Method used.
    :param url: The Referer header from the request.
    :param path: The HTTP Path used.
    :param query_string: The HTTP query string used.
    :param status: The HTTP Status code of the response.
    :param resource_id: The ID of the resource.
    :param sub_resource: The extracted subresource (user_token, etc)
    :param sub_resource_id: THe ID of the subresource.
    :param resource_before: The resource state before this event occurred.
    :param resource_after: The resource state after this event occurred.
    """
    global PUBLISHER

    if not PUBLISHER:
        CONF.register_opts(NOTIFICATION_OPTS, "notifications")
        PUBLISHER = Publisher(CONF.notifications)
        PUBLISHER.start()

    payload = {
        "author_id": author_id,
        "method": method,
        "url": url,
        "path": path,
        "query_string": query_string,
        "status": status,
        "resource": resource,
        "resource_id": resource_id,
        "sub_resource": sub_resource,
        "sub_resource_id": sub_resource_id,
        "resource_before": resource_before,
        "resource_after": resource_after
    }

    if resource:
        PUBLISHER.publish_message(resource, payload)
    else:
        LOG.warning("Attempted to send payload with no destination resource.")
