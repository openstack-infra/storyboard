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

from pecan import hooks

from storyboard.notifications.publisher import publish


class NotificationHook(hooks.PecanHook):
    def __init__(self):
        super(NotificationHook, self).__init__()

    def after(self, state):
        # Ignore get methods, we only care about changes.
        if state.request.method not in ['POST', 'PUT', 'DELETE']:
            return

        request = state.request
        response = state.response

        # Attempt to determine the type of the payload. This checks for
        # nested paths.
        (resource, resource_id, subresource, subresource_id) \
            = self._parse(request.path)
        if not resource:
            return

        if state.request.method == 'POST':
            # When a resource is created..
            response_body = json.loads(response.body)
            if response_body:
                resource_id = response_body.get('id')
            else:
                resource_id = None

        # Build the payload. Use of None is included to ensure that we don't
        # accidentally blow up the API call, but we don't anticipate it
        # happening.
        publish(author_id=request.current_user_id,
                method=request.method,
                path=request.path,
                status=response.status_code,
                resource=resource,
                resource_id=resource_id,
                sub_resource=subresource,
                sub_resource_id=subresource_id)

    def _parse(self, s):
        url_pattern = re.match("^\/v1\/([a-z_]+)\/?([0-9]+)?"
                               "\/?([a-z]+)?\/?([0-9]+)?$", s)
        if not url_pattern or url_pattern.groups()[0] == "openid":
            return None, None, None, None

        groups = url_pattern.groups()

        return groups[0], groups[1], groups[2], groups[3]
