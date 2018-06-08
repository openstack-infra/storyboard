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
import paho.mqtt.publish as mqtt_publish

from storyboard.notifications.mqtt import conf

CONF = cfg.CONF
CONF.register_opts(conf.MQTT_OPTS, group='mqtt_notifications')


class PushMQTT(object):
    def __init__(self, hostname, port=1883, client_id=None,
                 keepalive=60, will=None, auth=None, tls=None, qos=0):
        self.hostname = hostname
        self.port = port
        self.client_id = client_id
        self.keepalive = 60
        self.will = will
        self.auth = auth
        self.tls = tls
        self.qos = qos

    def publish_single(self, topic, msg):
        mqtt_publish.single(topic, msg, hostname=self.hostname,
                            port=self.port, client_id=self.client_id,
                            keepalive=self.keepalive, will=self.will,
                            auth=self.auth, tls=self.tls, qos=self.qos)

    def publish_multiple(self, topic, msg):
        mqtt_publish.multiple(topic, msg, hostname=self.hostname,
                              port=self.port, client_id=self.client_id,
                              keepalive=self.keepalive, will=self.will,
                              auth=self.auth, tls=self.tls, qos=self.qos)


def config_publisher():
    auth = None
    if CONF.mqtt_notifications.username:
        auth = {'username': CONF.mqtt_notifications.username,
                'password': CONF.mqtt_notifications.password}
    tls = None
    if CONF.mqtt_notifications.ca_certs:
        tls = {'ca_certs': CONF.mqtt_notifications.ca_certs,
               'certfile': CONF.mqtt_notifications.certfile,
               'keyfile': CONF.mqtt_notifications.keyfile}
    return PushMQTT(CONF.mqtt_notifications.hostname,
                    port=CONF.mqtt_notifications.port,
                    client_id=CONF.mqtt_notifications.client_id,
                    auth=auth, tls=tls, qos=CONF.mqtt_notifications.qos)


def _generate_topic(resource, resource_id=None, author_id=None,
                    sub_resource=None, sub_resource_id=None):
    topic = [CONF.mqtt_notifications.base_topic]
    if resource:
        topic.append(resource)
        if resource_id:
            topic.append(resource_id)
            if author_id:
                topic.append(author_id)
                if sub_resource:
                    topic.extend(['sub_resource', sub_resource])
                    if sub_resource_id:
                        topic.append(sub_resource_id)
    return '/'.join(topic)


def publish(resource, author_id=None, method=None, url=None, path=None,
            query_string=None, status=None, resource_id=None,
            sub_resource=None, sub_resource_id=None, resource_before=None,
            resource_after=None):
    mqtt_publish = config_publisher()
    topic = _generate_topic(resource, resource_id, author_id, sub_resource,
                            sub_resource_id)
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
    mqtt_publish.publish_single(topic, json.dumps(payload))
