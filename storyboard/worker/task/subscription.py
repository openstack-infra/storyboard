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

from storyboard.db.api import subscriptions
from storyboard.db.api import timeline_events
from storyboard.notifications.subscriptions_handler import handle_deletions
from storyboard.notifications.subscriptions_handler import handle_resources
from storyboard.notifications.subscriptions_handler import \
    handle_timeline_events
from storyboard.worker.task.base import WorkerTaskBase


class Subscription(WorkerTaskBase):
    def handle(self, author_id, method, path, status, resource, resource_id,
               sub_resource=None, sub_resource_id=None):
        """This worker handles API events and attempts to determine whether
        they correspond to user subscriptions.

        :param author_id: ID of the author's user record.
        :param method: The HTTP Method.
        :param path: The full HTTP Path requested.
        :param status: The returned HTTP Status of the response.
        :param resource: The resource type.
        :param resource_id: The ID of the resource.
        :param sub_resource: The subresource type.
        :param sub_resource_id: The ID of the subresource.
        """

        subscribers = subscriptions.subscription_get_all_subscriber_ids(
            resource, resource_id
        )

        if resource == 'timeline_events':
            event = timeline_events.event_get(resource_id)
            handle_timeline_events(event, author_id, subscribers)

        elif resource == 'project_groups':
            handle_resources(method=method,
                             resource_id=resource_id,
                             sub_resource_id=sub_resource_id,
                             author_id=author_id,
                             subscribers=subscribers)

        if method == 'DELETE' and not sub_resource_id:
            handle_deletions(resource, resource_id)

    def enabled(self):
        return True
