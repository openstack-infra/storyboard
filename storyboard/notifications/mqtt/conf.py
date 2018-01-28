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

from oslo_config import cfg


MQTT_OPTS = [
    cfg.StrOpt('hostname', help="MQTT broker address/name"),
    cfg.IntOpt('port', default=1883, help='MQTT broker port'),
    cfg.StrOpt('username',
               help="Username to authenticate against the broker."),
    cfg.StrOpt('password', secret=True,
               help='Password to authenticate against the broker.'),
    cfg.IntOpt('qos', default=0, min=0, max=2,
               help='Max MQTT QoS available on messages. This can be 0, 1, '
                    'or 2'),
    cfg.StrOpt('client_id',
               help='MQTT client identifier, default is hostname + pid'),
    cfg.StrOpt('base_topic', default='storyboard',
               help='The base MQTT topic to publish to'),
    cfg.StrOpt('ca_certs',
               help="The path to the Certificate Authority certificate files "
                    "that are to be treated as trusted. If this is the only "
                    "certificate option given then the client will operate in "
                    "a similar manner to a web browser. That is to say it will"
                    "require the broker to have a certificate signed by the "
                    "Certificate Authorities in ca_certs and will communicate "
                    "using TLS v1, but will not attempt any form of TLS"
                    "certificate based authentication."),
    cfg.StrOpt('certfile',
               help="The path pointing to the PEM encoded client certificate. "
                    "If this is set it will be used as client information for "
                    "TLS based authentication. Support for this feature is "
                    "broker dependent."),
    cfg.StrOpt('keyfile',
              help="The path pointing to the PEM encoded client private key."
                   "If this is set it will be used as client information for "
                   "TLS based authentication. Support for this feature is "
                   "broker dependent"),
]
