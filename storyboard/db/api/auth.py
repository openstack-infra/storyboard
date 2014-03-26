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

from storyboard.db.api import base as api_base
from storyboard.db import models


def authorization_code_get(code):
    query = api_base.model_query(models.AuthorizationCode,
                                 api_base.get_session())
    return query.filter_by(code=code, is_active=True).first()


def authorization_code_save(values):
    return api_base.entity_create(models.AuthorizationCode, values)


def authorization_code_delete(code):
    del_code = authorization_code_get(code)

    if del_code:
        del_code.is_active = False
        api_base.entity_update(models.AuthorizationCode, del_code.id,
                               del_code.as_dict())


def token_get(access_token):
    query = api_base.model_query(models.BearerToken, api_base.get_session())
    # Note: is_active filtering for a reason, because we may still need to
    # fetch expired token, for example to check refresh token info
    return query.filter_by(access_token=access_token).first()


def token_save(values):
    return api_base.entity_create(models.BearerToken, values)


def token_update(access_token, values):
    upd_token = token_get(access_token)

    if upd_token:
        return api_base.entity_update(models.BearerToken, upd_token.id, values)


def token_delete(access_token):
    del_token = token_get(access_token)

    if del_token:
        del_token.is_active = False
        api_base.entity_update(models.BearerToken, del_token.id,
                               del_token.as_dict())
