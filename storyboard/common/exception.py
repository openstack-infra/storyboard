# Copyright (c) 2014 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from storyboard.openstack.common.gettextutils import _  # noqa


class StoryboardException(Exception):
    """Base Exception for the project

    To correctly use this class, inherit from it and define
    the 'message' property.
    """

    message = _("An unknown exception occurred")

    def __str__(self):
        return self.message

    def __init__(self):
        super(StoryboardException, self).__init__(self.message)


class NotFound(StoryboardException):
    message = _("Object not found")

    def __init__(self, message=None):
        if message:
            self.message = message


class DuplicateEntry(StoryboardException):
    message = _("Database object already exists")

    def __init__(self, message=None):
        if message:
            self.message = message


class NotEmpty(StoryboardException):
    message = _("Database object must be empty")

    def __init__(self, message=None):
        if message:
            self.message = message
