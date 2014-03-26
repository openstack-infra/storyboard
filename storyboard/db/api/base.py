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

import copy

from oslo.config import cfg
import six

from storyboard.common import exception as exc
from storyboard.db import models
from storyboard.openstack.common.db import exception as db_exc
from storyboard.openstack.common.db.sqlalchemy import session as db_session
from storyboard.openstack.common.db.sqlalchemy.utils import paginate_query
from storyboard.openstack.common import log

CONF = cfg.CONF
CONF.import_group("database", "storyboard.openstack.common.db.options")
LOG = log.getLogger(__name__)
_FACADE = None

BASE = models.Base


def setup_db():
    try:
        engine = get_engine()
        BASE.metadata.create_all(engine)
    except Exception as e:
        LOG.exception("Database registration exception: %s", e)
        return False
    return True


def drop_db():
    try:
        BASE.metadata.drop_all(get_engine())
    except Exception as e:
        LOG.exception("Database shutdown exception: %s", e)
        return False
    return True


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


def entity_get(kls, entity_id, filter_non_public=False):
    entity = __entity_get(kls, entity_id, get_session())

    if filter_non_public:
        entity = _filter_non_public_fields(entity, entity._public_fields)

    return entity


def entity_get_all(kls, filter_non_public=False, marker=None, limit=None,
                   **kwargs):

    # Sanity check on input parameters
    kwargs = dict((k, v) for k, v in kwargs.iteritems() if v)

    # Construct the query
    query = model_query(kls).filter_by(**kwargs)
    query = paginate_query(query=query,
                           model=kls,
                           limit=limit,
                           sort_keys=['id'],
                           marker=marker,
                           sort_dir='asc')

    # Execute the query
    entities = query.all()
    if len(entities) > 0 and filter_non_public:
        sample_entity = entities[0] if len(entities) > 0 else None
        public_fields = getattr(sample_entity, "_public_fields", [])

        entities = [_filter_non_public_fields(entity, public_fields)
                    for entity in entities]

    return entities


def entity_get_count(kls, **kwargs):
    kwargs = dict((k, v) for k, v in kwargs.iteritems() if v)

    count = model_query(kls).filter_by(**kwargs).count()

    return count


def _filter_non_public_fields(entity, public_list=list()):
    ent_copy = copy.copy(entity)
    for attr_name, val in six.iteritems(entity.__dict__):
        if attr_name.startswith("_"):
            continue

        if attr_name not in public_list:
            delattr(ent_copy, attr_name)

    return ent_copy


def entity_create(kls, values):
    entity = kls()
    entity.update(values.copy())

    session = get_session()
    with session.begin():
        try:
            session.add(entity)
        except db_exc.DBDuplicateEntry:
            raise exc.DuplicateEntry("Duplicate entry for : %s"
                                     % kls.__name__)

    return entity


def entity_update(kls, entity_id, values):
    session = get_session()

    with session.begin():
        entity = __entity_get(kls, entity_id, session)
        if entity is None:
            raise exc.NotFound("%s %s not found" % (kls.__name__, entity_id))

        entity.update(values.copy())
        session.add(entity)

    return entity
