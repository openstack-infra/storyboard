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

from threading import Timer

import pika

from oslo_config import cfg
from oslo_log import log

from storyboard._i18n import _, _LI


CONF = cfg.CONF
LOG = log.getLogger(__name__)


class ConnectionService(object):
    """A generic amqp connection agent that handles unexpected
    interactions with RabbitMQ such as channel and connection closures,
    by reconnecting on failure.
    """

    def __init__(self, conf):
        """Setup the connection instance based on our configuration.

        :param conf A configuration object.
        """
        self._connection = None
        self._channel = None
        self._open = False
        self.started = False
        self._timer = None
        self._closing = False
        self._open_hooks = set()
        self._exchange_name = conf.rabbit_exchange_name
        self._application_id = conf.rabbit_application_name
        self._properties = pika.BasicProperties(
            app_id='storyboard', content_type='application/json')
        self._connection_credentials = pika.PlainCredentials(
            conf.rabbit_userid,
            conf.rabbit_password)
        self._connection_parameters = pika.ConnectionParameters(
            conf.rabbit_host,
            conf.rabbit_port,
            conf.rabbit_virtual_host,
            self._connection_credentials,
            connection_attempts=conf.rabbit_connection_attempts,
            retry_delay=conf.rabbit_retry_delay)

    def _connect(self):
        """This method connects to RabbitMQ, establishes a channel, declares
        the storyboard exchange if it doesn't yet exist, and executes any
        post-connection hooks that an extending class may have registered.
        """

        # If the closing flag is set, just exit.
        if self._closing:
            return

        # If a timer is set, kill it.
        if self._timer:
            LOG.debug(_('Clearing timer...'))
            self._timer.cancel()
            self._timer = None

        # Create the connection
        LOG.info(_LI('Connecting to %s'), self._connection_parameters.host)
        self._connection = pika.BlockingConnection(self._connection_parameters)

        # Create a channel
        LOG.debug(_('Creating a new channel'))
        self._channel = self._connection.channel()
        self._channel.confirm_delivery()

        # Declare the exchange
        LOG.debug(_('Declaring exchange %s'), self._exchange_name)
        self._channel.exchange_declare(exchange=self._exchange_name,
                                       exchange_type='topic',
                                       durable=True,
                                       auto_delete=False)

        # Set the open flag and execute any connection hooks.
        self._open = True
        self._execute_open_hooks()

    def _reconnect(self):
        """Reconnect to rabbit.
        """

        # Sanity check - if we're closing, do nothing.
        if self._closing:
            return

        # If a timer is already there, assume it's doing its thing...
        if self._timer:
            return
        LOG.debug(_('Scheduling reconnect in 5 seconds...'))
        self._timer = Timer(5, self._connect)
        self._timer.start()

    def _close(self):
        """This method closes the connection to RabbitMQ."""
        LOG.info(_LI('Closing connection'))
        self._open = False
        if self._channel:
            self._channel.close()
            self._channel = None
        if self._connection:
            self._connection.close()
            self._connection = None
        self._closing = False
        LOG.debug(_('Connection Closed'))

    def _execute_open_hooks(self):
        """Executes all hooks that have been registered to run on open.
        """
        for hook in self._open_hooks:
            hook()

    def start(self):
        """Start the publisher, opening a connection to RabbitMQ. This method
        must be explicitly invoked, otherwise any messages will simply be
        cached for later broadcast.
        """

        # Create the connection.
        self.started = True
        self._closing = False
        self._connect()

    def stop(self):
        """Stop the publisher by closing the channel and the connection.
        """
        self.started = False
        self._closing = True
        self._close()

    def add_open_hook(self, hook):
        """Add a method that will be executed whenever a connection is
        established.
        """
        self._open_hooks.add(hook)
