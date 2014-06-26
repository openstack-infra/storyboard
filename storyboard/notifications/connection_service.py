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

import pika

from oslo.config import cfg

from storyboard.notifications.conf import NOTIFICATION_OPTS
from storyboard.openstack.common import log

CONF = cfg.CONF
CONN = None

LOG = log.getLogger(__name__)


class ConnectionService:

    def __init__(self, conf):
        self.credentials = pika.PlainCredentials(
            conf.rabbit_userid,
            conf.rabbit_password)

        self.connection = pika.BlockingConnection(pika.ConnectionParameters(
            conf.rabbit_host,
            conf.rabbit_port,
            conf.rabbit_virtual_host,
            self.credentials))

    def create_exchange(self, channel, exchange, type):
        self.exchange = exchange
        self.type = type
        self.channel = channel
        self.channel.exchange_declare(exchange=self.exchange,
                                 type=self.type, durable=True)

    def close_connection(self):
        self.connection.close()


def initialize():
    # Initialize the AMQP event publisher.
    global CONN
    CONF.register_opts(NOTIFICATION_OPTS, "notifications")
    CONN = ConnectionService(CONF.notifications)


def get_connection():
    global CONN
    return CONN
