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

import abc


class WorkerTaskBase(object):
    """Base class for a worker that listens to events that occur within the
    API.
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, config):
        self.config = config

    @abc.abstractmethod
    def enabled(self):
        """A method which indicates whether this worker task is properly
        configured and should be enabled. If it's ready to go, return True.
        Otherwise, return False.
        """

    @abc.abstractmethod
    def handle(self, author_id, method, path, status, resource, resource_id,
               sub_resource=None, sub_resource_id=None,
               resource_before=None, resource_after=None):
        """Handle an event.

        :param author_id: ID of the author's user record.
        :param method: The HTTP Method.
        :param path: The full HTTP Path requested.
        :param status: The returned HTTP Status of the response.
        :param resource: The resource type.
        :param resource_id: The ID of the resource.
        :param sub_resource: The subresource type.
        :param sub_resource_id: The ID of the subresource.
        :param resource_before: The resource state before this event occurred.
        :param resource_after: The resource state after this event occurred.
        """
