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

from sqlalchemy.orm import subqueryload

from storyboard.db.api import base as api_base
from storyboard.db import models


def tag_get_by_id(id, session=None):
    if not session:
        session = api_base.get_session()
    query = session.query(models.StoryTag)\
        .options(subqueryload(models.StoryTag.stories))\
        .filter_by(id=id)

    return query.first()


def tag_get_by_name(name, session=None):
    if not session:
        session = api_base.get_session()
    query = session.query(models.StoryTag)\
        .options(subqueryload(models.StoryTag.stories))\
        .filter_by(name=name)

    return query.first()


def tag_get_all(name=None, marker=None, limit=None, offset=None):
    return api_base.entity_get_all(models.StoryTag,
                                   name=name,
                                   marker=marker,
                                   limit=limit,
                                   offset=offset)


def tag_get_count(**kwargs):
    return api_base.entity_get_count(models.StoryTag, **kwargs)


def tag_create(values):
    return api_base.entity_create(models.StoryTag, values)


def tag_update(tag_id, values):
    return api_base.entity_update(models.StoryTag, tag_id, values)
