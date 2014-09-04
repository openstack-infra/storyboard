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

from oslo.config import cfg
from pika.exceptions import ConnectionClosed

from storyboard.notifications.conf import NOTIFICATION_OPTS
from storyboard.notifications.connection_service import ConnectionService
from storyboard.openstack.common import log


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
        LOG.debug("Sending message to %s [%s]" % (self._exchange_name,
                                                  payload.topic))

        # First check, are we closing?
        if self._closing:
            LOG.warning("Cannot send message, publisher is closing.")
            if payload not in self._pending:
                self._pending.append(payload)
            return

        # Second check, are we open?
        if not self._open:
            LOG.debug("Cannot send message, publisher is connecting.")
            if payload not in self._pending:
                self._pending.append(payload)
            self._reconnect()
            return

        # Third check, are we in a sane state? This should never happen,
        # but just in case...
        if not self._connection or not self._channel:
            LOG.error("Cannot send message, publisher is an unexpected state.")
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
        except ConnectionClosed as cc:
            LOG.warning("Attempted to send message on closed connection.")
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


def publish(topic, payload):
    """Send a message with a given topic and payload to the storyboard
    exchange. The message will be automatically JSON encoded.

    :param topic: The RabbitMQ topic.
    :param payload: The JSON-serializable payload.
    :return:
    """
    global PUBLISHER

    if not PUBLISHER:
        CONF.register_opts(NOTIFICATION_OPTS, "notifications")
        PUBLISHER = Publisher(CONF.notifications)
        PUBLISHER.start()

    PUBLISHER.publish_message(topic, payload)
