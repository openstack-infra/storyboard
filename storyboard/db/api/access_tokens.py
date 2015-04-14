# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
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


def access_token_get(access_token_id, session=None):
    return api_base.entity_get(models.AccessToken,
                               access_token_id,
                               session=session)


def access_token_get_by_token(access_token):
    return api_base.model_query(models.AccessToken) \
        .filter_by(access_token=access_token).first()


def is_valid(access_token):
    if not access_token:
        return False

    token = access_token_get_by_token(access_token)

    if not token:
        return False

    if datetime.datetime.now(tz=pytz.utc) > token.expires_at:
        access_token_delete(token.id)
        return False

    return True


def access_token_get_all(marker=None, limit=None, sort_field=None,
                         sort_dir=None, **kwargs):
    # Sanity checks, in case someone accidentally explicitly passes in 'None'
    if not sort_field:
        sort_field = 'id'
    if not sort_dir:
        sort_dir = 'asc'

    # Construct the query
    query = access_token_build_query(**kwargs)

    query = api_base.paginate_query(query=query,
                                    model=models.AccessToken,
                                    limit=limit,
                                    sort_key=sort_field,
                                    marker=marker,
                                    sort_dir=sort_dir)

    # Execute the query
    return query.all()


def access_token_get_count(**kwargs):
    # Construct the query
    query = access_token_build_query(**kwargs)

    return query.count()


def access_token_create(values):
    # Update the expires_at date.
    values['created_at'] = datetime.datetime.now(pytz.utc)
    values['expires_at'] = datetime.datetime.now(pytz.utc) + datetime \
        .timedelta(seconds=values['expires_in'])

    return api_base.entity_create(models.AccessToken, values)


def access_token_update(access_token_id, values):
    values['expires_at'] = values['created_at'] + datetime.timedelta(
        seconds=values['expires_in'])

    return api_base.entity_update(models.AccessToken, access_token_id, values)


def access_token_build_query(**kwargs):
    # Construct the query
    query = api_base.model_query(models.AccessToken)

    # Apply the filters
    query = api_base.apply_query_filters(query=query,
                                         model=models.AccessToken,
                                         **kwargs)

    return query


def access_token_delete(access_token_id):
    session = api_base.get_session()

    with session.begin(subtransactions=True):
        access_token = access_token_get(access_token_id, session=session)

        if access_token:
            session.delete(access_token)


def access_token_delete_by_token(access_token):
    access_token = access_token_get_by_token(access_token)

    if access_token:
        access_token_delete(access_token.id)
