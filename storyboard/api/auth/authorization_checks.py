# Copyright (c) 2014 Mirantis Inc.
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
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pecan import abort
from pecan import request

from storyboard._i18n import _
from storyboard.db.api import access_tokens as token_api
from storyboard.db.api import users as user_api


def _get_token():
    if request.authorization and len(request.authorization) == 2:
        return request.authorization[1]
    else:
        return None


def guest():
    token = _get_token()

    # Public resources do not require a token.
    if not token:
        return True

    # But if there is a token, it should be valid.
    return token_api.is_valid(token)


def authenticated():
    token = _get_token()

    return token_api.is_valid(token)


def superuser():
    token = _get_token()

    if not token:
        return False

    token = token_api.access_token_get_by_token(token)

    if not token:
        return False

    user = user_api.user_get(token.user_id)

    if not user.is_superuser:
        abort(403, _("This action is limited to superusers only."))

    return user.is_superuser
