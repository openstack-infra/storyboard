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

import datetime
import pytz

from storyboard.db.api import base as api_base
from storyboard.db import models


def refresh_token_get(refresh_token_id, session=None):
    return api_base.entity_get(models.RefreshToken, refresh_token_id,
                               session=session)


def refresh_token_get_by_token(refresh_token):
    try:
        return api_base.model_query(models.RefreshToken) \
            .filter_by(refresh_token=refresh_token).first()
    except Exception:
        return None


def is_valid(refresh_token):
    if not refresh_token:
        return False

    token = refresh_token_get_by_token(refresh_token)

    if not token:
        return False

    if datetime.datetime.now(pytz.utc) > token.expires_at:
        refresh_token_delete(token.id)
        return False

    return True


def get_access_token_id(refresh_token_id):
    session = api_base.get_session()

    with session.begin(subtransactions=True):
        refresh_token = refresh_token_get(refresh_token_id, session)

        if refresh_token:
            return refresh_token.access_token.id


def refresh_token_create(values):
    session = api_base.get_session()

    with session.begin(subtransactions=True):
        values['expires_at'] = datetime.datetime.now(pytz.utc) + datetime.\
            timedelta(seconds=values['expires_in'])

        refresh_token = api_base.entity_create(models.RefreshToken, values)

        return refresh_token


def refresh_token_build_query(**kwargs):
    # Construct the query
    query = api_base.model_query(models.RefreshToken)

    # Apply the filters
    query = api_base.apply_query_filters(query=query,
                                         model=models.RefreshToken,
                                         **kwargs)

    return query


def refresh_token_delete(refresh_token_id):
    session = api_base.get_session()

    with session.begin(subtransactions=True):
        refresh_token = refresh_token_get(refresh_token_id)

        if refresh_token:
            session.delete(refresh_token)


def refresh_token_delete_by_token(refresh_token):
    refresh_token = refresh_token_get_by_token(refresh_token)

    if refresh_token:
        refresh_token_delete(refresh_token.id)
