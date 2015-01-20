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

import time

from oslo.config import cfg
from oslo_log import log
from pika.exceptions import ConnectionClosed
from stevedore import enabled

from storyboard.notifications.conf import NOTIFICATION_OPTS
from storyboard.notifications.connection_service import ConnectionService
from storyboard.openstack.common.gettextutils import _, _LW  # noqa


CONF = cfg.CONF
LOG = log.getLogger(__name__)


def subscribe():
    log.register_options(CONF)
    log.setup(CONF, 'storyboard')
    CONF(project='storyboard')
    CONF.register_opts(NOTIFICATION_OPTS, "notifications")

    subscriber = Subscriber(CONF.notifications)
    subscriber.start()

    manager = enabled.EnabledExtensionManager(
        namespace='storyboard.worker.task',
        check_func=check_enabled,
        invoke_on_load=True,
        invoke_args=(CONF,)
    )

    while subscriber.started:
        (method, properties, body) = subscriber.get()

        if not method or not properties:
            LOG.debug(_("No messages available, sleeping for 5 seconds."))
            time.sleep(5)
            continue

        manager.map(handle_event, body)

        # Ack the message
        subscriber.ack(method.delivery_tag)


def handle_event(ext, body):
    """Handle an event from the queue.

    :param ext: The extension that's handling this event.
    :param body: The body of the event.
    :return: The result of the handler.
    """
    return ext.obj.handle(body)


def check_enabled(ext):
    """Check to see whether an extension should be enabled.

    :param ext: The extension instance to check.
    :return: True if it should be enabled. Otherwise false.
    """
    return ext.obj.enabled()


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
            LOG.warning(_LW("Attempted to get message on closed connection."))
            LOG.debug(cc)
            self._open = False
            self._reconnect()
            return None, None, None
