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
import re

from oslo.config import cfg

from storyboard.notifications import connection_service
from storyboard.openstack.common import log

CONF = cfg.CONF

LOG = log.getLogger(__name__)


def parse(s):
    url_pattern = re.match("^\/v1\/([a-z_]+)\/?([0-9]+)?"
                           "\/?([a-z]+)?\/?([0-9]+)?$", s)
    if url_pattern and url_pattern.groups()[0] != "openid":
        return url_pattern.groups()
    else:
        return


def publish(payload, resource):
    payload = json.dumps(payload)
    routing_key = resource
    conn = connection_service.get_connection()
    channel = conn.connection.channel()

    conn.create_exchange(channel, 'storyboard', 'topic')

    channel.basic_publish(exchange='storyboard',
                          routing_key=routing_key,
                          body=payload)

    channel.close()


def process(state):

    request = state.request
    req_method = request.method
    req_user_id = request.current_user_id
    req_path = request.path
    req_resource_grp = parse(req_path)

    if req_resource_grp:

        resource = req_resource_grp[0]

        if req_resource_grp[1]:
            resource_id = req_resource_grp[1]

        # When a resource is created..
        else:
            response_str = state.response.body
            response = json.loads(response_str)
            if response:
                resource_id = response.get('id')
            else:
                resource_id = None
        # when adding/removing projects to project_groups..
        if req_resource_grp[3]:
            sub_resource_id = req_resource_grp[3]
            payload = {
                "user_id": req_user_id,
                "method": req_method,
                "resource": resource,
                "resource_id": resource_id,
                "sub_resource_id": sub_resource_id
            }

        else:
            payload = {
                "user_id": req_user_id,
                "method": req_method,
                "resource": resource,
                "resource_id": resource_id
            }

        publish(payload, resource)

    else:
        return
