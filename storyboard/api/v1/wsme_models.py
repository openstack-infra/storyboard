# Copyright (c) 2013 Mirantis Inc.
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

from datetime import datetime
import six
import warnings
from wsme import types as wtypes

from oslo.config import cfg
from sqlalchemy.exc import SADeprecationWarning
import storyboard.db.models as sqlalchemy_models
from storyboard.openstack.common.db.sqlalchemy import session as db_session


CONF = cfg.CONF


class _Base(wtypes.Base):

    id = int
    created_at = datetime
    updated_at = datetime

    def __init__(self, **kwargs):
        for key, val in six.iteritems(kwargs):
            setattr(self, key, val)
        super(_Base, self).__init__(**kwargs)

    @classmethod
    def get(cls, **kwargs):
        query = cls.from_db(**kwargs)
        entry = query.first()

        return convert_to_wsme(cls, entry)

    @classmethod
    def get_all(cls, **kwargs):
        query = cls.from_db(**kwargs)
        entries = query.all()

        return [convert_to_wsme(cls, entry) for entry in entries]

    @classmethod
    def create(cls, session=None, wsme_entry=None):
        if not session:
            session = db_session.get_session(sqlite_fk=True)
        with session.begin():
            db_entry = convert_to_db_model(cls, wsme_entry, session)
            session.add(db_entry)

        return cls.get(id=db_entry.id)

    @classmethod
    def update(cls, key_property_name="id", key_property_value=None,
               wsme_entry=None):
        db_entry = cls.from_db(**{key_property_name: key_property_value})\
            .first()
        if not db_entry:
            return None

        session = db_session.get_session(sqlite_fk=True)
        with session.begin():
            updated_db_model = update_db_model(cls, db_entry, wsme_entry)
            session.add(updated_db_model)

        return cls.get(id=db_entry.id)

    @classmethod
    def add_item(cls, cont_key_name, cont_key_value, item_cls, item_key_name,
                 item_key_value, container_name):
        session = db_session.get_session(sqlite_fk=True)
        with session.begin():
            db_container_enty = cls.from_db(session=session,
                                            **{cont_key_name: cont_key_value})\
                .first()
            if not db_container_enty:
                return None

            db_add_item = item_cls.from_db(session=session,
                                           **{item_key_name: item_key_value}).\
                first()
            if not db_add_item:
                return None

            getattr(db_container_enty, container_name).append(db_add_item)
            session.add(db_container_enty)

        return cls.get(**{cont_key_name: cont_key_value})

    @classmethod
    def create_and_add_item(cls, cont_key_name, cont_key_value, item_cls,
                            item_value, container_name):

        wsme_item = item_cls.create(wsme_entry=item_value)
        if not wsme_item:
            return None

        return cls.add_item(cont_key_name, cont_key_value, item_cls, "id",
                            wsme_item.id, container_name)

    @classmethod
    def from_db(cls, session=None, **kwargs):
        model_cls = WSME_TO_SQLALCHEMY[cls]
        if not session:
            session = db_session.get_session(sqlite_fk=True)
        query = session.query(model_cls)

        return query.filter_by(**kwargs)


warnings.simplefilter("ignore", SADeprecationWarning)


def convert_to_wsme(cls, entry):
    if not entry:
        return None

    wsme_object = cls()
    for attr in cls._wsme_attributes:
        attr_name = attr.name
        value = getattr(entry, attr_name)

        if value is None:
            continue

        if isinstance(attr._get_datatype(), _Base):
            value = convert_to_wsme(SQLALCHEMY_TO_WSME[type(attr)], value)

        if isinstance(attr._get_datatype(), wtypes.ArrayType):
            value = [convert_to_wsme(SQLALCHEMY_TO_WSME[type(item)], item)
                for item in value]
        setattr(wsme_object, attr_name, value)

    return wsme_object


def convert_to_db_model(cls, entry, session):
    if not entry:
        return None

    model_cls = WSME_TO_SQLALCHEMY[cls]

    model_object = model_cls()
    for attr in cls._wsme_attributes:
        attr_name = attr.name
        value = getattr(entry, attr_name)

        if value is None or isinstance(value, wtypes.UnsetType):
            continue

        if isinstance(attr._get_datatype(), _Base):
            value = convert_to_db_model(type(attr), value, session)
            session.add(value)

        if isinstance(attr._get_datatype(), wtypes.ArrayType):
            value = [convert_to_db_model(attr._get_datatype().item_type,
                                         item,
                                         session)
                for item in value]
        setattr(model_object, attr_name, value)

    return model_object


def update_db_model(cls, db_entry, wsme_entry):
    if not db_entry or not wsme_entry:
        return None

    for attr in cls._wsme_attributes:
        attr_name = attr.name
        value = getattr(wsme_entry, attr_name)

        if isinstance(value, wtypes.UnsetType):
            continue

        setattr(db_entry, attr_name, value)

    return db_entry


class ProjectGroup(_Base):
    """Represents a group of projects."""

    name = wtypes.text
    """A unique name, used in URLs, identifying the project group. All
    lowercase, no special characters. Examples: infra, compute.
    """

    title = wtypes.text
    """The full name of the project group, which can contain spaces, special
    characters, etc.
    """

    @classmethod
    def sample(cls):
        return cls(
            name="Infra",
            title="Awesome project")


class Permission(_Base):
    """Permissions can be associated with users and teams."""
    pass


class StoryTag(_Base):
    """Tags are used classifying user-stories."""
    pass


# TODO(ruhe): clarify and document what are 'action' and 'type' for
class Comment(_Base):
    """Represents a comment."""

    #todo(nkonovalov): replace with a enum
    action = wtypes.text
    """Comment action. Allowed values: unknown."""

    comment_type = wtypes.text
    """Comment type. Allowed values: unknown."""

    content = wtypes.text
    """All the text/plain chunks joined together as a unicode string."""

    story_id = int
    """ID of corresponding user-story."""

    author_id = int
    """Comment author ID."""

    @classmethod
    def sample(cls):
        return cls(
            action="action",
            comment_type="type1",
            content="comment content goes here",
            story_id=42,
            author_id=67)


class Team(_Base):
    pass


SQLALCHEMY_TO_WSME = {
    sqlalchemy_models.ProjectGroup: ProjectGroup,
    sqlalchemy_models.Permission: Permission,
    sqlalchemy_models.Comment: Comment,
    sqlalchemy_models.StoryTag: StoryTag
}

# database mappings
WSME_TO_SQLALCHEMY = dict(
    (v, k) for k, v in six.iteritems(SQLALCHEMY_TO_WSME)
)
