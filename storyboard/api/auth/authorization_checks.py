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

from pecan import request

from storyboard.api.auth.token_storage import storage
from storyboard.db import api as dbapi


def guest():
    return True


def authenticated():
    token_storage = storage.get_storage()

    result = False
    if request.authorization and len(request.authorization) == 2:
        token = request.authorization[1]
        if token and token_storage.check_access_token(token):
            result = True

    return result


def superuser():
    token_storage = storage.get_storage()

    if not authenticated():
        return False

    token = request.authorization[1]
    token_info = token_storage.get_access_token_info(token)
    user = dbapi.user_get(token_info.user_id)

    return user.is_superuser
