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

import ast
import time

from oslo.config import cfg
from pika.exceptions import ConnectionClosed

from storyboard.db.api import timeline_events
from storyboard.notifications.conf import NOTIFICATION_OPTS
from storyboard.notifications.connection_service import ConnectionService
from storyboard.notifications.subscriptions_handler import handle_deletions
from storyboard.notifications.subscriptions_handler import handle_resources
from storyboard.notifications.subscriptions_handler import \
    handle_timeline_events
from storyboard.openstack.common import log


CONF = cfg.CONF
LOG = log.getLogger(__name__)


def subscribe():
    log.setup('storyboard')
    CONF(project='storyboard')
    CONF.register_opts(NOTIFICATION_OPTS, "notifications")

    subscriber = Subscriber(CONF.notifications)
    subscriber.start()

    while subscriber.started:
        (method, properties, body) = subscriber.get()

        if not method or not properties:
            LOG.debug("No messages available, sleeping for 5 seconds.")
            time.sleep(5)
            continue

        body_dict = ast.literal_eval(body)
        if 'event_id' in body_dict:
            event_id = body_dict['event_id']
            event = timeline_events.event_get(event_id)
            handle_timeline_events(event)

        else:
            if body_dict['resource'] == 'project_groups':
                if 'sub_resource_id' in body_dict:
                    handle_resources(body_dict['method'],
                                     body_dict['resource_id'],
                                     body_dict['sub_resource_id'])
                else:
                    handle_resources(body_dict['method'],
                                     body_dict['resource_id'])

        if body_dict['method'] == 'DELETE':
            resource_name = body_dict['resource']
            resource_id = body_dict['resource_id']
            if 'sub_resource_id' not in body_dict:
                handle_deletions(resource_name, resource_id)

        # Handle the message
        subscriber.ack(method.delivery_tag)


class Subscriber(ConnectionService):
    def __init__(self, conf):
        """Setup the subscriber instance based on our configuration.

        :param conf A configuration object.
        """
        super(Subscriber, self).__init__(conf)

        self._queue_name = conf.rabbit_event_queue_name
        self._binding_keys = ['tasks', 'stories', 'projects', 'project_groups',
                              'timeline_events']
        self.add_open_hook(self._declare_queue)

    def _declare_queue(self):
        """Declare the subscription queue against our exchange.
        """
        self._channel.queue_declare(queue=self._queue_name,
                                    durable=True)

        # Set up the queue bindings.
        for binding_key in self._binding_keys:
            self._channel.queue_bind(exchange=self._exchange_name,
                                     queue=self._queue_name,
                                     routing_key=binding_key)

    def ack(self, delivery_tag):
        """Acknowledge receipt and processing of the message.
        """
        self._channel.basic_ack(delivery_tag)

    def get(self):
        """Get a single message from the queue. If the subscriber is currently
        waiting to reconnect, it will return None. Note that you must
        manually ack the message after it has been successfully processed.

        :rtype: (None, None, None)|(spec.Basic.Get,
                                    spec.Basic.Properties,
                                    str or unicode)
        """

        # Sanity check one, are we closing?
        if self._closing:
            return None, None, None

        # Sanity check two, are we open, or reconnecting?
        if not self._open:
            return None, None, None

        try:
            return self._channel.basic_get(queue=self._queue_name,
                                           no_ack=False)
        except ConnectionClosed as cc:
            LOG.warning("Attempted to get message on closed connection.")
            LOG.debug(cc)
            self._open = False
            self._reconnect()
            return None, None, None
