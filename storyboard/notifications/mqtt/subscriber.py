# Copyright 2018 IBM Corp.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import json

from oslo_config import cfg
import paho.mqtt.client as mqtt
from stevedore import enabled

from storyboard.notifications.mqtt import conf

CONF = cfg.CONF
CONF.register_opts(conf.MQTT_OPTS, group='mqtt_notifications')


def handle_event(ext, body):
    """Handle an event from the queue.

    :param ext: The extension that's handling this event.
    :param body: The body of the event.
    :return: The result of the handler.
    """
    payload = json.loads(body)
    return ext.obj.event(author_id=payload['author_id'] or None,
                         method=payload['method'] or None,
                         url=payload['url'] or None,
                         path=payload['path'] or None,
                         query_string=payload['query_string'] or None,
                         status=payload['status'] or None,
                         resource=payload['resource'] or None,
                         resource_id=payload['resource_id'] or None,
                         sub_resource=payload['sub_resource'] or None,
                         sub_resource_id=payload['sub_resource_id'] or None,
                         resource_before=payload['resource_before'] or None,
                         resource_after=payload['resource_after'] or None)


def check_enabled(ext):
    """Check to see whether an extension should be enabled.

    :param ext: The extension instance to check.
    :return: True if it should be enabled. Otherwise false.
    """
    return ext.obj.enabled()


def subscriber(topic=None):
    if not topic:
        topic = CONF.mqtt_notifications.base_topic + '/#'
    auth = None
    if CONF.mqtt_notifications.username:
        auth = {'username': CONF.mqtt_notifications.username,
                'password': CONF.mqtt_notifications.password}
    tls = None
    if CONF.mqtt_notifications.ca_certs:
        tls = {'ca_certs': CONF.mqtt_notifications.ca_certs,
               'certfile': CONF.mqtt_notifications.certfile,
               'keyfile': CONF.mqtt_notifications.keyfile}
    client = mqtt.Client()
    if tls:
        client.tls_set(**tls)
    if auth:
        client.username_pw_set(auth['username'],
                               password=auth.get('password'))

    manager = enabled.EnabledExtensionManager(
        namespace='storyboard.plugin.worker',
        check_func=check_enabled,
        invoke_on_load=True,
        invoke_args=(CONF,))

    def on_connect(client, userdata, flags, rc):
        # If no topic is specified subscribe to all messages on base_topic
        client.subscribe(topic, qos=CONF.mqtt_notifications.qos)

    def on_message(client, userdata, msg):
        manager.map(handle_event, msg.payload)

    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(CONF.mqtt_notifications.hostname,
                   CONF.mqtt_notifications.port)
    client.loop_forever()
