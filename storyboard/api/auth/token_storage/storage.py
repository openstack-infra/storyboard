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

import abc

from oslo.config import cfg

CONF = cfg.CONF

STORAGE_OPTS = [
    cfg.StrOpt('token_storage_type',
               default='mem',
               help='Authorization token storage type.'
                    ' The only supported type is "mem".'
                    ' tbd: db storage')
]

CONF.register_opts(STORAGE_OPTS)


class StorageBase(object):

    @abc.abstractmethod
    def save_authorization_code(self, authorization_code, user_id):
        pass

    @abc.abstractmethod
    def check_authorization_code(self, code):
        pass

    @abc.abstractmethod
    def get_authorization_code_info(self, code):
        pass

    @abc.abstractmethod
    def invalidate_authorization_code(self, code):
        pass

    @abc.abstractmethod
    def save_token(self, access_token, expires_in, refresh_token, user_id):
        pass

    @abc.abstractmethod
    def check_access_token(self, access_token):
        pass

    @abc.abstractmethod
    def get_access_token_info(self, access_token):
        pass

    @abc.abstractmethod
    def remove_token(self, token):
        pass


STORAGE = None


def get_storage():
    global STORAGE
    return STORAGE


def set_storage(impl):
    global STORAGE
    STORAGE = impl
