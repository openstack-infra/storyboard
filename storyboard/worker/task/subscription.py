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
# implied. See the License for the specific language governing permissions and
# limitations under the License.

import json

from storyboard.db.api import timeline_events
from storyboard.notifications.subscriptions_handler import handle_deletions
from storyboard.notifications.subscriptions_handler import handle_resources
from storyboard.notifications.subscriptions_handler import \
    handle_timeline_events
from storyboard.worker.task.base import WorkerTaskBase


class Subscription(WorkerTaskBase):
    def handle(self, body):
        """This worker handles API events and attempts to determine whether
        they correspond to user subscriptions.

        :param body: The event message body.
        :return:
        """
        body_dict = json.loads(body)
        if 'event_id' in body_dict:
            event_id = body_dict['event_id']
            event = timeline_events.event_get(event_id)
            handle_timeline_events(event, body_dict['author_id'])

        else:
            if body_dict['resource'] == 'project_groups':
                if 'sub_resource_id' in body_dict:
                    handle_resources(method=body_dict['method'],
                                     resource_id=body_dict['resource_id'],
                                     sub_resource_id=body_dict[
                                         'sub_resource_id'],
                                     author_id=body_dict['author_id'])
                else:
                    handle_resources(method=body_dict['method'],
                                     resource_id=body_dict['resource_id'],
                                     author_id=body_dict['author_id'])

        if body_dict['method'] == 'DELETE':
            resource_name = body_dict['resource']
            resource_id = body_dict['resource_id']
            if 'sub_resource_id' not in body_dict:
                handle_deletions(resource_name, resource_id)

    def enabled(self):
        return True
