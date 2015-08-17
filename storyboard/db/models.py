# Copyright 2013 Hewlett-Packard Development Company, L.P.
# Copyright 2013 Thierry Carrez <thierry@openstack.org>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""
SQLAlchemy Models for storing storyboard
"""

import datetime
import pytz
import six
import six.moves.urllib.parse as urlparse

from oslo_config import cfg
from oslo_db.sqlalchemy import models
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy.dialects.mysql import MEDIUMTEXT
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
from sqlalchemy_fulltext import FullText

from storyboard.common import event_types
from storyboard.db.decorators import UTCDateTime

CONF = cfg.CONF


def table_args():
    engine_name = urlparse.urlparse(cfg.CONF.database_connection).scheme
    if engine_name == 'mysql':
        return {'mysql_engine': cfg.CONF.mysql_engine,
                'mysql_charset': "utf8"}
    return None

# # CUSTOM TYPES

# A mysql medium text type.
MYSQL_MEDIUM_TEXT = UnicodeText().with_variant(MEDIUMTEXT(), 'mysql')


class CommonLength:
    top_large_length = 255
    top_middle_length = 100
    top_short_length = 50
    lower_large_length = 5
    lower_middle_length = 3
    lower_short_length = 1
    name_length = 30


class IdMixin(object):
    id = Column(Integer, primary_key=True)


class UTCTimestampMixin(object):
    """A Database model mixin that automatically manages our creation and
    updating timestamps. This mixin was copied from oslo_db, and adapted to
    use our own internal UTCDateTime type decorator.
    """
    created_at = Column(UTCDateTime,
                        default=lambda: datetime.datetime.now(tz=pytz.utc))
    updated_at = Column(UTCDateTime,
                        onupdate=lambda: datetime.datetime.now(tz=pytz.utc))


class StoriesBase(UTCTimestampMixin,
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


class ModelBuilder(object):
    def __init__(self, **kwargs):
        super(ModelBuilder, self).__init__()

        if kwargs:
            for key in kwargs:
                if key in self:
                    self[key] = kwargs[key]


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


class User(FullText, ModelBuilder, Base):
    __table_args__ = (
        schema.UniqueConstraint('email', name='uniq_user_email'),
    )

    __fulltext_columns__ = ['full_name', 'email']

    full_name = Column(Unicode(CommonLength.top_large_length), nullable=True)
    email = Column(String(CommonLength.top_large_length))
    openid = Column(String(CommonLength.top_large_length))
    is_staff = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    last_login = Column(UTCDateTime)
    teams = relationship("Team", secondary="team_membership")
    permissions = relationship("Permission", secondary="user_permissions")
    enable_login = Column(Boolean, default=True)

    preferences = relationship("UserPreference")

    _public_fields = ["id", "openid", "full_name", "last_login",
                      "enable_login"]


class UserPreference(ModelBuilder, Base):
    __tablename__ = 'user_preferences'

    _TASK_TYPES = ('string', 'int', 'bool', 'float')

    user_id = Column(Integer, ForeignKey('users.id'))
    key = Column(Unicode(CommonLength.top_middle_length))
    value = Column(Unicode(CommonLength.top_large_length))
    type = Column(Enum(*_TASK_TYPES), default='string')

    @property
    def cast_value(self):
        try:
            cast_func = {
                'float': lambda x: float(x),
                'int': lambda x: int(x),
                'bool': lambda x: bool(x),
                'string': lambda x: six.text_type(x)
            }[self.type]

            return cast_func(self.value)
        except ValueError:
            return self.value

    @cast_value.setter
    def cast_value(self, value):
        if isinstance(value, bool):
            self.type = 'bool'
        elif isinstance(value, int):
            self.type = 'int'
        elif isinstance(value, float):
            self.type = 'float'
        else:
            self.type = 'string'

        self.value = six.text_type(value)

    _public_fields = ["id", "key", "value", "type"]


class Team(ModelBuilder, Base):
    __table_args__ = (
        schema.UniqueConstraint('name', name='uniq_team_name'),
    )
    name = Column(Unicode(CommonLength.top_large_length))
    users = relationship("User", secondary="team_membership")
    permissions = relationship("Permission", secondary="team_permissions")


project_group_mapping = Table(
    'project_group_mapping', Base.metadata,
    Column('project_id', Integer, ForeignKey('projects.id')),
    Column('project_group_id', Integer, ForeignKey('project_groups.id')),
)


may_mutate_to = Table(
    'may_mutate_to', Base.metadata,
    Column('story_type_id_from', Integer, ForeignKey('story_types.id'),
           nullable=False),
    Column('story_type_id_to', Integer, ForeignKey('story_types.id'),
           nullable=False),
    schema.UniqueConstraint('story_type_id_from', 'story_type_id_to')
)


class StoryType(ModelBuilder, Base):
    __tablename__ = 'story_types'

    name = Column(String(CommonLength.top_middle_length))
    icon = Column(String(CommonLength.top_middle_length))
    restricted = Column(Boolean, default=False)
    private = Column(Boolean, default=False)
    visible = Column(Boolean, default=True)

    _public_fields = ["id", "name", "icon", "restricted", "private",
                      "visible"]


class Permission(ModelBuilder, Base):
    __table_args__ = (
        schema.UniqueConstraint('name', name='uniq_permission_name'),
    )
    name = Column(Unicode(CommonLength.top_short_length))
    codename = Column(Unicode(CommonLength.top_large_length))


# TODO(mordred): Do we really need name and title?
class Project(FullText, ModelBuilder, Base):
    """Represents a software project."""

    __table_args__ = (
        schema.UniqueConstraint('name', name='uniq_project_name'),
    )

    __fulltext_columns__ = ['name', 'description']

    name = Column(String(CommonLength.top_short_length))
    description = Column(UnicodeText())
    team_id = Column(Integer, ForeignKey('teams.id'))
    team = relationship(Team, primaryjoin=team_id == Team.id)
    tasks = relationship('Task', backref='project')
    branches = relationship('Branch', backref='project')
    repo_url = Column(String(CommonLength.top_large_length), default=None)
    is_active = Column(Boolean, default=True)
    project_groups = relationship("ProjectGroup",
                                  secondary="project_group_mapping")
    autocreate_branches = Column(Boolean, default=False)

    _public_fields = ["id", "name", "description", "tasks", "repo_url",
                      "autocreate_branches"]


class ProjectGroup(ModelBuilder, Base):
    __tablename__ = 'project_groups'
    __table_args__ = (
        schema.UniqueConstraint('name', name='uniq_group_name'),
    )

    name = Column(String(CommonLength.top_short_length))
    title = Column(Unicode(CommonLength.top_large_length))
    projects = relationship("Project", secondary="project_group_mapping")

    _public_fields = ["id", "name", "title", "projects"]


story_storytags = Table(
    'story_storytags', Base.metadata,
    Column('story_id', Integer, ForeignKey('stories.id')),
    Column('storytag_id', Integer, ForeignKey('storytags.id')),
)


class Story(FullText, ModelBuilder, Base):
    __tablename__ = 'stories'

    __fulltext_columns__ = ['title', 'description']

    creator_id = Column(Integer, ForeignKey('users.id'))
    story_type_id = Column(Integer, ForeignKey('story_types.id'),
                           default=1)
    creator = relationship(User, primaryjoin=creator_id == User.id)
    title = Column(Unicode(CommonLength.top_large_length))
    description = Column(UnicodeText())
    is_bug = Column(Boolean, default=True)
    tasks = relationship('Task', backref='story')
    events = relationship('TimeLineEvent', backref='story')
    tags = relationship('StoryTag', secondary='story_storytags')

    _public_fields = ["id", "creator_id", "title", "description", "is_bug",
                      "tasks", "events", "tags"]


class Task(FullText, ModelBuilder, Base):
    __fulltext_columns__ = ['title']

    TASK_STATUSES = {'todo': 'Todo',
                     'merged': 'Merged',
                     'invalid': 'Invalid',
                     'review': 'Review',
                     'inprogress': 'Progress'}

    _TASK_PRIORITIES = ('low', 'medium', 'high')

    creator_id = Column(Integer, ForeignKey('users.id'))
    title = Column(Unicode(CommonLength.top_large_length), nullable=True)
    status = Column(Enum(*TASK_STATUSES.keys()), default='todo')
    story_id = Column(Integer, ForeignKey('stories.id'))
    project_id = Column(Integer, ForeignKey('projects.id'))
    assignee_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    branch_id = Column(Integer, ForeignKey('branches.id'), nullable=True)
    milestone_id = Column(Integer, ForeignKey('milestones.id'), nullable=True)
    priority = Column(Enum(*_TASK_PRIORITIES), default='medium')

    _public_fields = ["id", "creator_id", "title", "status", "story_id",
                      "project_id", "assignee_id", "priority", "branch_id",
                      "milestone_id"]


class Branch(ModelBuilder, Base):
    __tablename__ = 'branches'

    __table_args__ = (
        schema.UniqueConstraint('name', 'project_id', name='branch_un_constr'),
    )

    name = Column(String(CommonLength.top_middle_length))
    tasks = relationship('Task', backref='branch')
    milestones = relationship('Milestone', backref='branch')
    project_id = Column(Integer, ForeignKey('projects.id'))
    expired = Column(Boolean, default=False)
    expiration_date = Column(UTCDateTime, default=None)
    autocreated = Column(Boolean, default=False)
    restricted = Column(Boolean, default=False)

    _public_fields = ["id", "name", "project_id", "expired",
                      "expiration_date", "autocreated"]


class Milestone(ModelBuilder, Base):
    __tablename__ = 'milestones'

    __table_args__ = (
        schema.UniqueConstraint('name', 'branch_id',
                                name='milestone_un_constr'),
    )

    name = Column(String(CommonLength.top_middle_length))
    tasks = relationship('Task', backref='milestone')
    branch_id = Column(Integer, ForeignKey('branches.id'))
    expired = Column(Boolean, default=False)
    expiration_date = Column(UTCDateTime, default=None)

    _public_fields = ["id", "name", "branch_id", "expired", "expiration_date"]


class StoryTag(ModelBuilder, Base):
    __tablename__ = 'storytags'
    __table_args__ = (
        schema.UniqueConstraint('name', name='uniq_story_tags_name'),
    )
    name = Column(String(CommonLength.top_short_length))
    stories = relationship('StoryTag', secondary='story_storytags')


# Authorization models

class AuthorizationCode(ModelBuilder, Base):
    code = Column(Unicode(CommonLength.top_middle_length), nullable=False)
    state = Column(Unicode(CommonLength.top_middle_length), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    expires_in = Column(Integer, nullable=False, default=300)


class AccessToken(ModelBuilder, Base):
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    access_token = Column(Unicode(CommonLength.top_middle_length),
                          nullable=False)
    expires_in = Column(Integer, nullable=False)
    expires_at = Column(UTCDateTime, nullable=False)
    refresh_token = relationship("RefreshToken",
                                 uselist=False,
                                 cascade="all, delete-orphan",
                                 backref="access_token",
                                 passive_updates=False,
                                 passive_deletes=False)


class RefreshToken(ModelBuilder, Base):
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    access_token_id = Column(Integer,
                             ForeignKey('accesstokens.id'),
                             nullable=False)
    refresh_token = Column(Unicode(CommonLength.top_middle_length),
                           nullable=False)
    expires_in = Column(Integer, nullable=False)
    expires_at = Column(UTCDateTime, nullable=False)


def _story_build_summary_query():
    # first create a subquery for task statuses
    select_items = []
    select_items.append(Story)
    select_items.append(
        expr.case(
            [(func.sum(Task.status.in_(
                ['todo', 'inprogress', 'review'])) > 0,
              'active'),
             ((func.sum(Task.status == 'merged')) > 0, 'merged')],
            else_='invalid'
        ).label('status')
    )
    for task_status in Task.TASK_STATUSES:
        select_items.append(expr.cast(
            func.sum(Task.status == task_status), Integer
        ).label(task_status))
    select_items.append(expr.null().label('task_statuses'))

    result = select(select_items, None,
                    expr.Join(Story, Task, onclause=Story.id == Task.story_id,
                              isouter=True)) \
        .group_by(Story.id) \
        .alias('story_summary')

    return result


class StorySummary(Base):
    __table__ = _story_build_summary_query()
    tags = relationship('StoryTag', secondary='story_storytags')

    def as_dict(self):
        d = super(StorySummary, self).as_dict()
        d["tags"] = [t.name for t in self.tags]

        return d

    _public_fields = ["id", "creator_id", "title", "description", "is_bug",
                      "tasks", "comments", "tags", "status",
                      "task_statuses"]


# Time-line models

class TimeLineEvent(ModelBuilder, Base):
    __tablename__ = 'events'

    story_id = Column(Integer, ForeignKey('stories.id'))
    comment_id = Column(Integer, ForeignKey('comments.id'), nullable=True)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=True)

    event_type = Column(Enum(*event_types.ALL), nullable=False)

    # this info field should contain additional fields to describe the event
    # ex. {'old_status': 'Todo', 'new_status': 'In progress'}
    # or {'old_assignee_id': 1, 'new_assignee_id': 42}
    event_info = Column(UnicodeText(), nullable=True)


class Comment(FullText, ModelBuilder, Base):
    __fulltext_columns__ = ['content']

    content = Column(MYSQL_MEDIUM_TEXT)
    is_active = Column(Boolean, default=True)


# Subscription and notifications

class Subscription(ModelBuilder, Base):
    _SUBSCRIPTION_TARGETS = ('task', 'story', 'project', 'project_group')

    user_id = Column(Integer, ForeignKey('users.id'))
    target_type = Column(Enum(*_SUBSCRIPTION_TARGETS))

    # Cant use foreign key here as it depends on the type
    target_id = Column(Integer)

    _public_fields = ["id", "target_type", "target_id", "user_id"]


class SubscriptionEvents(ModelBuilder, Base):
    __tablename__ = 'subscription_events'

    subscriber_id = Column(Integer, ForeignKey('users.id'))
    author_id = Column(Integer, ForeignKey('users.id'))
    event_type = Column(Unicode(CommonLength.top_middle_length),
                        nullable=False)
    event_info = Column(UnicodeText(), nullable=True)


# Worklists and boards

class WorklistItem(ModelBuilder, Base):
    __tablename__ = "worklist_items"

    _ITEM_TYPES = ("story", "task")

    list_id = Column(Integer, ForeignKey('worklists.id'), nullable=False)
    list_position = Column(Integer, nullable=False)
    item_type = Column(Enum(*_ITEM_TYPES), nullable=False)
    item_id = Column(Integer, nullable=False)

    _public_fields = ["id", "list_id", "list_position", "item_type",
                      "item_id"]


class WorklistCriteria(FullText, ModelBuilder, Base):
    __tablename__ = "worklist_criteria"
    __fulltext_columns__ = ['title']

    title = Column(Unicode(CommonLength.top_middle_length), nullable=True)
    list_id = Column(Integer, ForeignKey('worklists.id'), nullable=False)
    value = Column(Unicode(CommonLength.top_short_length), nullable=False)
    field = Column(Unicode(CommonLength.top_short_length), nullable=False)

    _public_fields = ["id", "title", "list_id", "value", "field"]


class Worklist(FullText, ModelBuilder, Base):
    __tablename__ = "worklists"
    __fulltext_columns__ = ['title']

    title = Column(Unicode(CommonLength.top_middle_length), nullable=True)
    creator_id = Column(Integer, ForeignKey('users.id'))
    project_id = Column(Integer, ForeignKey('projects.id'))
    permission_id = Column(Integer, ForeignKey('permissions.id'))
    private = Column(Boolean, default=False)
    archived = Column(Boolean, default=False)
    automatic = Column(Boolean, default=False)
    items = relationship(WorklistItem)
    criteria = relationship(WorklistCriteria)

    _public_fields = ["id", "title", "creator_id", "project_id",
                      "permission_id", "private", "archived", "automatic"]


class BoardWorklist(ModelBuilder, Base):
    __tablename__ = 'board_worklists'

    board_id = Column(Integer, ForeignKey('boards.id'))
    list_id = Column(Integer, ForeignKey('worklists.id'))
    position = Column(Integer)
    worklist = relationship(Worklist)

    _public_fields = ["id", "board_id", "list_id", "position"]


class Board(FullText, ModelBuilder, Base):
    __tablename__ = "boards"
    __fulltext_columns__ = ['title', 'description']

    title = Column(Unicode(CommonLength.top_middle_length), nullable=False)
    description = Column(UnicodeText(), nullable=True)
    creator_id = Column(Integer, ForeignKey('users.id'))
    project_id = Column(Integer, ForeignKey('projects.id'))
    permission_id = Column(Integer, ForeignKey('permissions.id'))
    private = Column(Boolean, default=False)
    archived = Column(Boolean, default=False)
    lanes = relationship(BoardWorklist)

    _public_fields = ["id", "title", "description", "creator_id",
                      "project_id", "permission_id", "private", "archived"]
