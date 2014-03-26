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

from storyboard.api.auth.token_storage import storage
from storyboard.db.api import auth as auth_api


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
        values = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": expires_in,
            "expires_at": datetime.datetime.now() + datetime.timedelta(
                seconds=expires_in),
            "user_id": user_id
        }

        auth_api.token_save(values)

    def get_access_token_info(self, access_token):
        return auth_api.token_get(access_token)

    def check_access_token(self, access_token):
        token_info = auth_api.token_get(access_token)

        if not token_info:
            return False

        if datetime.datetime.now() > token_info.expires_at:
            auth_api.token_update(access_token, {"is_active": False})
            return False

        return token_info.is_active

    def remove_token(self, access_token):
        auth_api.token_delete(access_token)
