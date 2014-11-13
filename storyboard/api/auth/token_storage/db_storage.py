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

import datetime

from oslo.config import cfg

from storyboard.api.auth.token_storage import storage
from storyboard.db.api import access_tokens as token_api
from storyboard.db.api import auth as auth_api


CONF = cfg.CONF


class DBTokenStorage(storage.StorageBase):
    def save_authorization_code(self, authorization_code, user_id):
        values = {
            "code": authorization_code["code"],
            "state": authorization_code["state"],
            "user_id": user_id
        }
        auth_api.authorization_code_save(values)

    def get_authorization_code_info(self, code):
        return auth_api.authorization_code_get(code)

    def check_authorization_code(self, code):
        db_code = auth_api.authorization_code_get(code)
        return not db_code is None

    def invalidate_authorization_code(self, code):
        auth_api.authorization_code_delete(code)

    def save_token(self, access_token, expires_in, refresh_token, user_id):
        access_token_values = {
            "access_token": access_token,
            "expires_in": expires_in,
            "expires_at": datetime.datetime.now() + datetime.timedelta(
                seconds=expires_in),
            "user_id": user_id
        }

        # Oauthlib does not provide a separate expiration time for a
        # refresh_token so taking it from config directly.
        refresh_expires_in = CONF.refresh_token_ttl

        refresh_token_values = {
            "refresh_token": refresh_token,
            "user_id": user_id,
            "expires_in": refresh_expires_in,
            "expires_at": datetime.datetime.now() + datetime.timedelta(
                seconds=refresh_expires_in),
        }

        token_api.access_token_create(access_token_values)
        auth_api.refresh_token_save(refresh_token_values)

    def get_access_token_info(self, access_token):
        return token_api.access_token_get_by_token(access_token)

    def check_access_token(self, access_token):
        token_info = token_api.access_token_get_by_token(access_token)

        if not token_info:
            return False

        if datetime.datetime.now() > token_info.expires_at:
            token_api.access_token_delete(access_token)
            return False

        return True

    def remove_token(self, access_token):
        token_api.access_token_delete(access_token)

    def check_refresh_token(self, refresh_token):
        refresh_token_entry = auth_api.refresh_token_get(refresh_token)

        if not refresh_token_entry:
            return False

        if datetime.datetime.now() > refresh_token_entry.expires_at:
            auth_api.refresh_token_delete(refresh_token)
            return False

        return True

    def get_refresh_token_info(self, refresh_token):
        return auth_api.refresh_token_get(refresh_token)

    def invalidate_refresh_token(self, refresh_token):
        auth_api.refresh_token_delete(refresh_token)
