# Copyright (c) 2015 Mirantis Inc.
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

from storyboard.db.api import access_tokens as access_tokens_api
from storyboard.db.api import base as api_base
from storyboard.db import models


def user_token_get(access_token_id):
    return api_base.model_query(models.AccessToken) \
        .filter_by(id=access_token_id).first()


def user_token_get_all(marker=None, limit=None, sort_field=None,
                       sort_dir=None, **kwargs):
    if not sort_field:
        sort_field = 'id'
    if not sort_dir:
        sort_dir = 'asc'

    query = api_base.model_query(models.AccessToken)

    query = api_base.apply_query_filters(query=query,
                                         model=models.AccessToken,
                                         **kwargs)

    query = api_base.paginate_query(query=query,
                                    model=models.AccessToken,
                                    limit=limit,
                                    sort_key=sort_field,
                                    marker=marker,
                                    sort_dir=sort_dir)

    return query.all()


def user_token_get_count(**kwargs):
    query = api_base.model_query(models.AccessToken)

    query = api_base.apply_query_filters(query=query,
                                         model=models.AccessToken,
                                         **kwargs)

    return query.count()


def user_token_create(values):
    access_token = access_tokens_api.access_token_create(values)

    return user_token_get(access_token.id)


def user_token_update(access_token_id, values):
    access_token = access_tokens_api.access_token_update(
        access_token_id,
        values)

    if access_token:
        return user_token_get(access_token.id)
    else:
        return None


def user_token_delete(access_token_id):
    access_tokens_api.access_token_delete(access_token_id)


def delete_all_user_tokens(user_id):
    access_tokens = access_tokens_api.access_token_get_all(user_id=user_id)

    for token in access_tokens:
        access_tokens_api.access_token_delete(token.id)
