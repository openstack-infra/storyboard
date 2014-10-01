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
    def handle(self, body):
        """Handle an event."""
