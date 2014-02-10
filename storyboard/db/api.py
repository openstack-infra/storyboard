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


## BEGIN Projects

def _project_get(project_id, session):
    query = model_query(models.Project, session)
    return query.filter_by(id=project_id).first()


def project_get(project_id):
    return _project_get(project_id, get_session())


def project_get_all(**kwargs):
    query = model_query(models.Project)
    return query.filter_by(**kwargs).all()


def project_create(values):
    project = models.Project()
    project.update(values.copy())

    session = get_session()
    with session.begin():
        try:
            project.save(session=session)
        except db_exc.DBDuplicateEntry as e:
            raise exc.DuplicateEntry("Duplicate entry for Project: %s"
                                     % e.columns)

    return project


def project_update(project_id, values):
    session = get_session()

    with session.begin():
        project = _project_get(project_id, session)
        if project is None:
            raise exc.NotFound("Project %s not found" % project_id)

        project.update(values.copy())

    return project


## BEGIN Stories

def _story_get(story_id, session):
    query = model_query(models.Story, session)
    return query.filter_by(id=story_id).first()


def story_get_all(**kwargs):
    query = model_query(models.Story)
    return query.filter_by(**kwargs).all()


def story_get(story_id):
    return _story_get(story_id, get_session())


def story_create(values):
    story = models.Story()
    story.update(values.copy())

    session = get_session()
    with session.begin():
        try:
            story.save(session)
        except db_exc.DBDuplicateEntry as e:
            raise exc.DuplicateEntry("Duplicate etnry for Story: %s"
                                     % e.colums)

    return story


def story_update(story_id, values):
    session = get_session()

    with session.begin():
        story = _story_get(story_id, session)
        if story is None:
            raise exc.NotFound("Story %s not found" % story_id)

        story.update(values.copy())

    return story
