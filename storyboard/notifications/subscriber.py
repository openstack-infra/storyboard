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

from oslo.config import cfg

from storyboard.db.api import timeline_events
from storyboard.notifications import connection_service
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

    connection_service.initialize()

    conn = connection_service.get_connection()
    channel = conn.connection.channel()

    conn.create_exchange(channel, 'storyboard', 'topic')

    result = channel.queue_declare(queue='subscription_queue', durable=True)
    queue_name = result.method.queue

    binding_keys = ['tasks', 'stories', 'projects', 'project_groups',
                    'timeline_events']
    for binding_key in binding_keys:
        channel.queue_bind(exchange='storyboard',
                           queue=queue_name,
                           routing_key=binding_key)

    def callback(ch, method, properties, body):
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

    channel.basic_consume(callback,
                          queue=queue_name,
                          no_ack=True)

    channel.start_consuming()
