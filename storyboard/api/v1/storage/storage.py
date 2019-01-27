# Copyright (c) 2019 Adam Coldrick
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

import abc

from oslo_config import cfg


CONF = cfg.CONF

STORAGE_OPTS = [
    cfg.BoolOpt("enable_attachments",
                default=False,
                help="Enable (or disable) the attachments API"),
    cfg.StrOpt("storage_backend",
               default="swift",
               help="Storage backend implementation to use. Currently only"
                    "`swift` is supported."),
]

CONF.register_opts(STORAGE_OPTS, 'attachments')


class StorageBackend(object):
    """Interface which must be implemented by attachment storage backends."""

    @abc.abstractmethod
    def get_upload_url(self):
        pass

    @abc.abstractmethod
    def get_auth(self):
        pass


STORAGE_BACKEND = None


def get_storage_backend():
    global STORAGE_BACKEND
    return STORAGE_BACKEND


def set_storage_backend(impl):
    global STORAGE_BACKEND
    STORAGE_BACKEND = impl
