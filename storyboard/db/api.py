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
CONF.import_group("database", "storyboard.openstack.common.db.options")
LOG = log.getLogger(__name__)
_FACADE = None


def _get_facade_instance():
    """Generate an instance of the DB Facade.
    """
    global _FACADE
    if _FACADE is None:
        _FACADE = db_session.EngineFacade(
            CONF.database.connection,
            **dict(CONF.database.iteritems()))
    return _FACADE


def _destroy_facade_instance():
    """Destroys the db facade instance currently in use.
    """
    global _FACADE
    _FACADE = None


def get_engine():
    """Returns the global instance of our database engine.
    """
    facade = _get_facade_instance()
    return facade.get_engine()


def get_session(autocommit=True, expire_on_commit=False):
    """Returns a database session from our facade.
    """
    facade = _get_facade_instance()
    return facade.get_session(autocommit=autocommit,
                              expire_on_commit=expire_on_commit)


def cleanup():
    """Manually clean up our database engine.
    """
    _destroy_facade_instance()


def model_query(model, session=None):
    """Query helper.

    :param model: base model to query
    """
    session = session or get_session()
    query = session.query(model)
    return query


def __entity_get(kls, entity_id, session):
    query = model_query(kls, session)
    return query.filter_by(id=entity_id, is_active=True).first()


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
            session.add(entity)
        except db_exc.DBDuplicateEntry:
            raise exc.DuplicateEntry("Duplicate entry for : %s"
                                     % (kls.__name__))

    return entity


def _entity_update(kls, entity_id, values):
    session = get_session()

    with session.begin():
        entity = __entity_get(kls, entity_id, session)
        if entity is None:
            raise exc.NotFound("%s %s not found" % (kls.__name__, entity_id))

        entity.update(values.copy())
        session.add(entity)

    return entity


## BEGIN Users

def user_get(user_id):
    return _entity_get(models.User, user_id)


def user_get_all():
    return _entity_get_all(models.User)


def user_get_by_openid(openid):
    query = model_query(models.User, get_session())
    return query.filter_by(openid=openid).first()


def user_create(values):
    user = models.User()
    user.update(values.copy())

    session = get_session()
    with session.begin():
        try:
            user.save(session=session)
        except db_exc.DBDuplicateEntry as e:
            raise exc.DuplicateEntry("Duplicate entry for User: %s"
                                     % e.columns)

    return user


def user_update(user_id, values):
    session = get_session()

    with session.begin():
        user = _entity_get(models.User, user_id)
        if user is None:
            raise exc.NotFound("User %s not found" % user_id)

        user.update(values.copy())

    return user


## BEGIN Projects

def project_get(project_id):
    return _entity_get(models.Project, project_id)


def project_get_all(**kwargs):
    return _entity_get_all(models.Project, is_active=True)


def project_create(values):
    return _entity_create(models.Project, values)


def project_update(project_id, values):
    return _entity_update(models.Project, project_id, values)


def project_delete(project_id):
    project = project_get(project_id)

    if project:
        project.is_active = False
        _entity_update(models.Project, project_id, project.as_dict())


# BEGIN Stories

def story_get(story_id):
    return _entity_get(models.Story, story_id)


def story_get_all(project_id=None):
    if project_id:
        return story_get_all_in_project(project_id)
    else:
        return _entity_get_all(models.Story, is_active=True)


def story_get_all_in_project(project_id):
    session = get_session()

    query = model_query(models.Story, session).join(models.Task)
    return query.filter(models.Task.project_id == project_id,
                        models.Story.is_active)


def story_create(values):
    return _entity_create(models.Story, values)


def story_update(story_id, values):
    return _entity_update(models.Story, story_id, values)


def story_delete(story_id):
    story = story_get(story_id)

    if story:
        story.is_active = False
        _entity_update(models.Story, story_id, story.as_dict())


# BEGIN Tasks

def task_get(task_id):
    return _entity_get(models.Task, task_id)


def task_get_all(story_id=None):
    return _entity_get_all(models.Task, story_id=story_id, is_active=True)


def task_create(values):
    return _entity_create(models.Task, values)


def task_update(task_id, values):
    return _entity_update(models.Task, task_id, values)


def task_delete(task_id):
    task = task_get(task_id)

    if task:
        task.is_active = False
        _entity_update(models.Task, task_id, task.as_dict())
