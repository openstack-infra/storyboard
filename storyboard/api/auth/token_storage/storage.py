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
               default='db',
               help='Authorization token storage type.'
                    ' Supported types are "mem" and "db".'
                    ' Memory storage is not persistent between api launches')
]

CONF.register_opts(STORAGE_OPTS)


class StorageBase(object):

    @abc.abstractmethod
    def save_authorization_code(self, authorization_code, user_id):
        """This method should save an Authorization Code to the storage and
        associate it with a user_id.

        @param authorization_code: An object, containing state and a the code
            itself.
        @param user_id: The id of a User to associate the code with.
        """
        pass

    @abc.abstractmethod
    def check_authorization_code(self, code):
        """Check that the given token exists in the storage.

        @param code: The code to be checked.
        @return bool
        """
        pass

    @abc.abstractmethod
    def get_authorization_code_info(self, code):
        """Get the code info from the storage.

        @param code: An authorization Code

        @return object: The returned object should contain the state and the
            user_id, which the given code is associated with.
        """
        pass

    @abc.abstractmethod
    def invalidate_authorization_code(self, code):
        """Remove a code from the storage.

        @param code: An authorization Code
        """
        pass

    @abc.abstractmethod
    def save_token(self, access_token, expires_in, refresh_token, user_id):
        """Save a Bearer token to the storage with all associated fields

        @param access_token: A token that will be used in authorized requests.
        @param expires_in: The time in seconds while the access_token is valid.
        @param refresh_token: A token that will be used in a refresh request
            after an access_token gets expired.
        @param user_id: The id of a User which owns a token.
        """
        pass

    @abc.abstractmethod
    def check_access_token(self, access_token):
        """This method should say if a given token exists in the storage and
        that it has not expired yet.

        @param access_token: The token to be checked.
        @return bool
        """
        pass

    @abc.abstractmethod
    def get_access_token_info(self, access_token):
        """Get the Bearer token from the storage.

        @param access_token: The token to get the information about.
        @return object: The object should contain all fields associated with
            the token (refresh_token, expires_in, user_id).
        """
        pass

    @abc.abstractmethod
    def remove_token(self, token):
        """Invalidate a given token and remove it from the storage.

        @param token: The token to be removed.
        """
        pass

    @abc.abstractmethod
    def check_refresh_token(self, refresh_token):
        """This method should say if a given token exists in the storage and
        that it has not expired yet.

        @param refresh_token: The token to be checked.
        @return bool
        """
        pass

    @abc.abstractmethod
    def get_refresh_token_info(self, refresh_token):
        """Get the Bearer token from the storage.

        @param refresh_token: The token to get the information about.
        @return object: The object should contain all fields associated with
            the token (refresh_token, expires_in, user_id).
        """
        pass

    @abc.abstractmethod
    def invalidate_refresh_token(self, refresh_token):
        """Remove a token from the storage.

        @param refresh_token: A refresh token
        """
        pass


STORAGE = None


def get_storage():
    global STORAGE
    return STORAGE


def set_storage(impl):
    global STORAGE
    STORAGE = impl
