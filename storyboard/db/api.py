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

from oslo.config import cfg

from storyboard.common import exception as exc
from storyboard.db import models
from storyboard.openstack.common.db import exception as db_exc
from storyboard.openstack.common.db.sqlalchemy import session as db_session
from storyboard.openstack.common import log

CONF = cfg.CONF
LOG = log.getLogger(__name__)

get_session = db_session.get_session


def model_query(model, session=None):
    """Query helper.

    :param model: base model to query
    """
    session = session or get_session()
    query = session.query(model)
    return query


def __entity_get(kls, entity_id, session):
    query = model_query(kls, session)
    return query.filter_by(id=entity_id).first()


def _entity_get(kls, entity_id):
    return __entity_get(kls, entity_id, get_session())


def _entity_get_all(kls, **kwargs):
    kwargs = dict((k, v) for k, v in kwargs.iteritems() if v)

    query = model_query(kls)
    return query.filter_by(**kwargs).all()


def _entity_create(kls, values):
    entity = kls()
    entity.update(values.copy())

    session = get_session()
    with session.begin():
        try:
            entity.save(session=session)
        except db_exc.DBDuplicateEntry as e:
            raise exc.DuplicateEntry("Duplicate etnry for : %s"
                                     % (kls.__name__, e.colums))

    return entity


def entity_update(kls, entity_id, values):
    session = get_session()

    with session.begin():
        entity = __entity_get(kls, entity_id, session)
        if entity is None:
            raise exc.NotFound("%s %s not found" % (kls.__name__, entity_id))

        entity.update(values.copy())

    return entity


## BEGIN Projects

def project_get(project_id):
    return _entity_get(models.Project, project_id)


def project_get_all(**kwargs):
    return _entity_get_all(models.Project, **kwargs)


def project_create(values):
    return _entity_create(models.Project, values)


def project_update(project_id, values):
    return entity_update(models.Project, project_id, values)


## BEGIN Stories


def story_get(story_id):
    return _entity_get(models.Story, story_id)


def story_get_all(project_id=None):
    if project_id:
        return story_get_all_in_project(project_id)
    else:
        return _entity_get_all(models.Story)


def story_get_all_in_project(project_id):
    session = get_session()

    query = model_query(models.Story, session).join(models.Task)
    return query.filter_by(project_id=project_id)


def story_create(values):
    return _entity_create(models.Story, values)


def story_update(story_id, values):
    return entity_update(models.Story, story_id, values)


# BEGIN Tasks

def task_get(task_id):
    return _entity_get(models.Task, task_id)


def task_get_all(story_id=None):
    return _entity_get_all(models.Task, story_id=story_id)


def task_create(values):
    return _entity_create(models.Task, values)


def task_update(task_id, values):
    return entity_update(models.Task, task_id, values)
