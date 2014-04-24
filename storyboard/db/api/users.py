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

from storyboard.common import exception as exc
from storyboard.db.api import base as api_base
from storyboard.db import models
from storyboard.openstack.common.db import exception as db_exc


def user_get(user_id, filter_non_public=False):
    entity = api_base.entity_get(models.User, user_id,
                                 filter_non_public=filter_non_public)

    return entity


def user_get_all(marker=None, limit=None, filter_non_public=False,
                 **kwargs):
    return api_base.entity_get_all(models.User,
                                   marker=marker,
                                   limit=limit,
                                   filter_non_public=filter_non_public,
                                   **kwargs)


def user_get_count(**kwargs):
    return api_base.entity_get_count(models.User, **kwargs)


def user_get_by_openid(openid):
    query = api_base.model_query(models.User, api_base.get_session())
    return query.filter_by(openid=openid).first()


def user_create(values):
    user = models.User()
    user.update(values.copy())

    session = api_base.get_session()
    with session.begin():
        try:
            user.save(session=session)
        except db_exc.DBDuplicateEntry as e:
            raise exc.DuplicateEntry("Duplicate entry for User: %s"
                                     % e.columns)

    return user


def user_update(user_id, values):
    return api_base.entity_update(models.User, user_id, values)
