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

from oslo.config import cfg
from storyboard.notifications import connection_service
from storyboard.openstack.common import log

CONF = cfg.CONF
LOG = log.getLogger(__name__)


def subscribe():

    CONF(project='storyboard')
    connection_service.initialize()
    conn = connection_service.get_connection()
    channel = conn.connection.channel()
    conn.create_exchange(channel, 'storyboard', 'topic')
    result = channel.queue_declare(exclusive=True)
    queue_name = result.method.queue
    binding_keys = ['projects', 'tasks', 'stories', 'timeline_events']

    for binding_key in binding_keys:
        channel.queue_bind(exchange='storyboard',
                           queue=queue_name,
                           routing_key=binding_key)

    def callback(ch, method, properties, body):
        print(" [x] %r %r %r %r"
              % (method.routing_key, body, ch, properties))

    channel.basic_consume(callback,
                          queue=queue_name,
                          no_ack=True)

    channel.start_consuming()
