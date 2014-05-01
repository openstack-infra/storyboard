# Copyright 2013 Hewlett-Packard Development Company, L.P.
# Copyright 2013 Thierry Carrez <thierry@openstack.org>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""
SQLAlchemy Models for storing storyboard
"""

from oslo.config import cfg
import six.moves.urllib.parse as urlparse
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Enum
from sqlalchemy.ext import declarative
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy.orm import relationship
from sqlalchemy import schema
from sqlalchemy import select
import sqlalchemy.sql.expression as expr
import sqlalchemy.sql.functions as func
from sqlalchemy import String
from sqlalchemy import Table
from sqlalchemy import Unicode
from sqlalchemy import UnicodeText

from storyboard.openstack.common.db.sqlalchemy import models

CONF = cfg.CONF


def table_args():
    engine_name = urlparse.urlparse(cfg.CONF.database_connection).scheme
    if engine_name == 'mysql':
        return {'mysql_engine': cfg.CONF.mysql_engine,
                'mysql_charset': "utf8"}
    return None


class IdMixin(object):
    id = Column(Integer, primary_key=True)


class StoriesBase(models.TimestampMixin,
                  IdMixin,
                  models.ModelBase):
    metadata = None

    @declarative.declared_attr
    def __tablename__(cls):
        # NOTE(jkoelker) use the pluralized name of the class as the table
        return cls.__name__.lower() + 's'

    def as_dict(self):
        d = {}
        for c in self.__table__.columns:
            d[c.name] = self[c.name]
        return d


Base = declarative.declarative_base(cls=StoriesBase)

user_permissions = Table(
    'user_permissions', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('permission_id', Integer, ForeignKey('permissions.id')),
)

team_permissions = Table(
    'team_permissions', Base.metadata,
    Column('team_id', Integer, ForeignKey('teams.id')),
    Column('permission_id', Integer, ForeignKey('permissions.id')),
)

team_membership = Table(
    'team_membership', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('team_id', Integer, ForeignKey('teams.id')),
)


class User(Base):
    __table_args__ = (
        schema.UniqueConstraint('username', name='uniq_user_username'),
        schema.UniqueConstraint('email', name='uniq_user_email'),
    )
    username = Column(Unicode(30))
    full_name = Column(Unicode(255), nullable=True)
    email = Column(String(255))
    openid = Column(String(255))
    is_staff = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    last_login = Column(DateTime)
    teams = relationship("Team", secondary="team_membership")
    permissions = relationship("Permission", secondary="user_permissions")

    _public_fields = ["id", "openid", "full_name", "username", "last_login"]


class Team(Base):
    __table_args__ = (
        schema.UniqueConstraint('name', name='uniq_team_name'),
    )
    name = Column(Unicode(255))
    users = relationship("User", secondary="team_membership")
    permissions = relationship("Permission", secondary="team_permissions")

project_group_mapping = Table(
    'project_group_mapping', Base.metadata,
    Column('project_id', Integer, ForeignKey('projects.id')),
    Column('project_group_id', Integer, ForeignKey('project_groups.id')),
)


class Permission(Base):
    __table_args__ = (
        schema.UniqueConstraint('name', name='uniq_permission_name'),
    )
    name = Column(Unicode(50))
    codename = Column(Unicode(255))


# TODO(mordred): Do we really need name and title?
class Project(Base):
    """Represents a software project."""

    __table_args__ = (
        schema.UniqueConstraint('name', name='uniq_project_name'),
    )

    name = Column(String(50))
    description = Column(UnicodeText())
    team_id = Column(Integer, ForeignKey('teams.id'))
    team = relationship(Team, primaryjoin=team_id == Team.id)
    tasks = relationship('Task', backref='project')
    is_active = Column(Boolean, default=True)

    _public_fields = ["id", "name", "description", "tasks"]


class ProjectGroup(Base):
    __tablename__ = 'project_groups'
    __table_args__ = (
        schema.UniqueConstraint('name', name='uniq_group_name'),
    )

    name = Column(String(50))
    title = Column(Unicode(100))
    projects = relationship("Project", secondary="project_group_mapping")


class Story(Base):
    __tablename__ = 'stories'

    creator_id = Column(Integer, ForeignKey('users.id'))
    creator = relationship(User, primaryjoin=creator_id == User.id)
    title = Column(Unicode(100))
    description = Column(UnicodeText())
    is_bug = Column(Boolean, default=True)
    tasks = relationship('Task', backref='story')
    events = relationship('TimeLineEvent', backref='story')
    tags = relationship('StoryTag', backref='story')

    _public_fields = ["id", "creator_id", "title", "description", "is_bug",
                      "tasks", "events", "tags"]


class Task(Base):
    _TASK_STATUSES = ('todo', 'inprogress', 'invalid', 'review', 'merged')
    _TASK_PRIORITIES = ('low', 'medium', 'high')

    creator_id = Column(Integer, ForeignKey('users.id'))
    title = Column(Unicode(100), nullable=True)
    status = Column(Enum(*_TASK_STATUSES), default='todo')
    story_id = Column(Integer, ForeignKey('stories.id'))
    project_id = Column(Integer, ForeignKey('projects.id'))
    assignee_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    priority = Column(Enum(*_TASK_PRIORITIES), default='medium')

    _public_fields = ["id", "creator_id", "title", "status", "story_id",
                      "project_id", "assignee_id", "priority"]


class StoryTag(Base):
    __table_args__ = (
        schema.UniqueConstraint('name', name='uniq_story_tags_name'),
    )
    name = Column(String(20))
    story_id = Column(Integer, ForeignKey('stories.id'))


# Authorization models

class AuthorizationCode(Base):

    code = Column(Unicode(100), nullable=False)
    state = Column(Unicode(100), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)


class AccessToken(Base):

    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    access_token = Column(Unicode(100), nullable=False)
    expires_in = Column(Integer, nullable=False)
    expires_at = Column(DateTime, nullable=False)


class RefreshToken(Base):

    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    refresh_token = Column(Unicode(100), nullable=False)


def _story_build_summary_query():
    return select([Story,
                   func.cast(
                       func.sum(Task.status == 'todo'), Integer
                   ).label('todo'),
                   func.cast(
                       func.sum(Task.status == 'inprogress'), Integer
                   ).label('inprogress'),
                   func.cast(
                       func.sum(Task.status == 'review'), Integer
                   ).label('review'),
                   func.cast(
                       func.sum(Task.status == 'merged'), Integer
                   ).label('merged'),
                   func.cast(
                       func.sum(Task.status == 'invalid'), Integer
                   ).label('invalid'),
                   expr.case(
                       [(func.sum(Task.status.in_(
                           ['todo', 'inprogress', 'review'])) > 0,
                         'active'),
                        ((func.sum(Task.status == 'merged')) > 0, 'merged')],
                       else_='invalid'
                   ).label('status')],
                  None,
                  expr.Join(Story, Task, onclause=Story.id == Task.story_id,
                            isouter=True)) \
        .group_by(Task.story_id) \
        .alias('story_summary')


class StorySummary(Base):
    __table__ = _story_build_summary_query()

    _public_fields = ["id", "creator_id", "title", "description", "is_bug",
                      "tasks", "comments", "tags", "todo", "inprogress",
                      "review", "merged", "invalid", "status"]


# Time-line models

class TimeLineEvent(Base):
    __tablename__ = 'events'

    story_id = Column(Integer, ForeignKey('stories.id'))
    comment_id = Column(Integer, ForeignKey('comments.id'), nullable=True)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=True)

    event_type = Column(Unicode(100), nullable=False)

    # this info field should contain additional fields to describe the event
    # ex. {'old_status': 'Todo', 'new_status': 'In progress'}
    # or {'old_assignee_id': 1, 'new_assignee_id': 42}
    event_info = Column(UnicodeText(), nullable=True)


class Comment(Base):

    content = Column(UnicodeText)
    is_active = Column(Boolean, default=True)
