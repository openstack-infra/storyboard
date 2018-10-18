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
#

"""initial version

Revision ID: 001
Revises: None
Create Date: 2013-12-10 00:35:55.327593

"""

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None


from alembic import op
from oslo_log import log
import sqlalchemy as sa
from sqlalchemy.sql.expression import table

from storyboard.db.models import MYSQL_MEDIUM_TEXT

LOG = log.getLogger(__name__)

MYSQL_ENGINE = 'InnoDB'
MYSQL_CHARSET = 'utf8'


def _define_enums():
    pref_type = sa.Enum('string', 'int', 'bool', 'float')

    task_priority = sa.Enum(
        'low', 'medium', 'high',
        name='task_priority')

    task_status = sa.Enum(
        'todo', 'inprogress', 'invalid', 'review', 'merged',
        name='task_status')

    target_type = sa.Enum(
        'task', 'story', 'project', 'project_group',
        name='target_type')

    return {
        'pref_type': pref_type,
        'target_type': target_type,
        'task_priority': task_priority,
        'task_status': task_status
    }


def upgrade(active_plugins=None, options=None):
    enums = _define_enums()

    op.create_table(
        'project_groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('name', sa.String(length=50), nullable=True),
        sa.Column('title', sa.Unicode(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uniq_group_name'),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )
    op.create_table(
        'user_preferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('key', sa.Unicode(100), nullable=False),
        sa.Column('type', enums['pref_type'], nullable=False),
        sa.Column('value', sa.Unicode(255), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('full_name', sa.Unicode(255), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('openid', sa.String(255)),
        sa.Column('is_staff', sa.Boolean(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=True),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('enable_login', sa.Boolean(), default=True,
                  server_default="1", nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='uniq_user_email'),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )
    op.create_table(
        'teams',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('name', sa.Unicode(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uniq_team_name'),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )
    op.create_table(
        'permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('name', sa.Unicode(length=50), nullable=True),
        sa.Column('codename', sa.Unicode(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uniq_permission_name'),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )
    op.create_table(
        'team_membership',
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('team_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint(),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )
    op.create_table(
        'user_permissions',
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('permission_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint(),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )
    op.create_table(
        'team_permissions',
        sa.Column('permission_id', sa.Integer(), nullable=True),
        sa.Column('team_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ),
        sa.PrimaryKeyConstraint(),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )
    op.create_table(
        'stories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('creator_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.Unicode(length=255), nullable=True),
        sa.Column('description', sa.UnicodeText(), nullable=True),
        sa.Column('is_bug', sa.Boolean(), nullable=True),
        sa.Column('story_type_id', sa.Integer(), default=1),
        sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('name', sa.String(length=50), nullable=True),
        sa.Column('description', sa.UnicodeText(), nullable=True),
        sa.Column('team_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True,
                  server_default='1', nullable=False),
        sa.Column('repo_url', sa.String(255), default=None, nullable=True),
        sa.Column('autocreate_branches', sa.Boolean(), default=False),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uniq_project_name'),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )
    op.create_table(
        'project_group_mapping',
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('project_group_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['project_group_id'], ['project_groups.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint(),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )
    op.create_table(
        'tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('title', sa.Unicode(length=255), nullable=True),
        sa.Column('status', enums['task_status'], nullable=True),
        sa.Column('story_id', sa.Integer(), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('assignee_id', sa.Integer(), nullable=True),
        sa.Column('creator_id', sa.Integer(), nullable=True),
        sa.Column('priority', enums['task_priority'], nullable=True),
        sa.Column('branch_id', sa.Integer(), nullable=True),
        sa.Column('milestone_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['assignee_id'], ['users.id'],
                                name='tasks_ibfk_1'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'],
                                name='tasks_ibfk_3'),
        sa.ForeignKeyConstraint(['story_id'], ['stories.id'],
                                name='tasks_ibfk_4'),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )
    op.create_table(
        'events',
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('story_id', sa.Integer(), nullable=True),
        sa.Column('comment_id', sa.Integer(), nullable=True),
        sa.Column('author_id', sa.Integer(), nullable=True),
        sa.Column('event_type', sa.Unicode(length=100), nullable=False),
        sa.Column('event_info', sa.UnicodeText(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )
    op.create_table(
        'comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('content', type_=MYSQL_MEDIUM_TEXT, nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True,
                  server_default='1', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )
    op.create_table(
        'storytags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('name', sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uniq_story_tags_name'),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )
    op.create_table('story_storytags',
        sa.Column('story_id', sa.Integer(), nullable=True),
        sa.Column('storytag_id', sa.Integer(), nullable=True),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )
    op.create_table(
        'subscriptions',
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('target_type', enums['target_type'], nullable=True),
        sa.Column('target_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )
    op.create_table(
        'subscription_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('subscriber_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.Unicode(100), nullable=False),
        sa.Column('event_info', sa.UnicodeText(), nullable=True),
        sa.Column('author_id', sa.Integer()),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )
    op.create_table(
        'authorizationcodes',
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.Unicode(100), nullable=False),
        sa.Column('state', sa.Unicode(100), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('expires_in', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )
    op.create_table(
        'accesstokens',
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('access_token', sa.Unicode(length=100), nullable=False),
        sa.Column('expires_in', sa.Integer(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        mysql_default_charset=MYSQL_CHARSET,
        mysql_engine=MYSQL_ENGINE
    )
    op.create_table(
        'refreshtokens',
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('refresh_token', sa.Unicode(length=100), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('expires_in', sa.Integer(), nullable=False),
        sa.Column('access_token_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        mysql_default_charset=MYSQL_CHARSET,
        mysql_engine=MYSQL_ENGINE
    )
    op.create_table(
        'branches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('expired', sa.Boolean(), default=False, nullable=True),
        sa.Column('expiration_date', sa.DateTime(), default=None,
                  nullable=True),
        sa.Column('autocreated', sa.Boolean(), default=False, nullable=True),
        sa.Column('restricted', sa.Boolean(), default=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', 'project_id', name="branch_un_constr"),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )
    op.create_table(
        'milestones',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=True),
        sa.Column('branch_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('expired', sa.Boolean(), default=False, nullable=True),
        sa.Column('expiration_date', sa.DateTime(), default=None),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', 'branch_id', name="milestone_un_constr"),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )
    op.create_table(
        'story_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('name', sa.String(50), nullable=True),
        sa.Column('icon', sa.String(50), nullable=True),
        sa.Column('restricted', sa.Boolean(), default=False),
        sa.Column('private', sa.Boolean(), default=False),
        sa.Column('visible', sa.Boolean(), default=True),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )
    op.create_table(
        'may_mutate_to',
        sa.Column('story_type_id_from', sa.Integer(), nullable=False),
        sa.Column('story_type_id_to', sa.Integer(), nullable=False),
        sa.UniqueConstraint('story_type_id_from',
                            'story_type_id_to',
                            name="mutate_un_constr"),
        sa.PrimaryKeyConstraint(),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )

    # Create story types
    bind = op.get_bind()
    story_types_table = table(
        'story_types',
        sa.Column('name', sa.String(50), nullable=True),
        sa.Column('icon', sa.String(50), nullable=True),
        sa.Column('restricted', sa.Boolean(), default=False),
        sa.Column('private', sa.Boolean(), default=False),
        sa.Column('visible', sa.Boolean(), default=True),
    )
    bind.execute(story_types_table.insert().values(
        name='bug',
        icon='fa-bug'
    ))
    bind.execute(story_types_table.insert().values(
        name='feature',
        icon='fa-lightbulb-o',
        restricted=True
    ))
    bind.execute(story_types_table.insert().values(
        name='private_vulnerability',
        icon='fa-lock',
        private=True
    ))
    bind.execute(story_types_table.insert().values(
        name='public_vulnerability',
        icon='fa-bomb',
        visible=False
    ))

    # Populate may_mutate_to
    may_mutate_to = table(
        'may_mutate_to',
        sa.Column('story_type_id_from', sa.Integer(), nullable=False),
        sa.Column('story_type_id_to', sa.Integer(), nullable=False),
    )
    bind.execute(may_mutate_to.insert().values(
        story_type_id_from=1,
        story_type_id_to=4
    ))
    bind.execute(may_mutate_to.insert().values(
        story_type_id_from=1,
        story_type_id_to=2
    ))
    bind.execute(may_mutate_to.insert().values(
        story_type_id_from=2,
        story_type_id_to=1
    ))
    bind.execute(may_mutate_to.insert().values(
        story_type_id_from=3,
        story_type_id_to=4
    ))
    bind.execute(may_mutate_to.insert().values(
        story_type_id_from=3,
        story_type_id_to=1
    ))
    bind.execute(may_mutate_to.insert().values(
        story_type_id_from=4,
        story_type_id_to=1
    ))

    op.create_index('accesstokens_access_token_idx',
                    'accesstokens', ['access_token'])

    version_info = op.get_bind().engine.dialect.server_version_info
    if version_info[-1] == "MariaDB":
        # Removes fake mysql prefix
        version_info = version_info[-4:]
    if version_info[0] < 5 or version_info[0] == 5 and version_info[1] < 6:
        LOG.warning(
            "MySQL version is lower than 5.6. Skipping full-text indexes")
        return

    # Index for projects
    op.execute("ALTER TABLE projects "
               "ADD FULLTEXT projects_fti (name, description)")

    # Index for stories
    op.execute("ALTER TABLE stories "
               "ADD FULLTEXT stories_fti (title, description)")

    # Index for tasks
    op.execute("ALTER TABLE tasks ADD FULLTEXT tasks_fti (title)")

    # Index for comments
    op.execute("ALTER TABLE comments ADD FULLTEXT comments_fti (content)")

    # Index for users
    op.execute("ALTER TABLE users ADD FULLTEXT users_fti (full_name, email)")


def downgrade(active_plugins=None, options=None):
    # be careful with the order, keep FKs in mind
    op.drop_table('project_group_mapping')
    op.drop_table('team_membership')
    op.drop_table('team_permissions')
    op.drop_table('user_permissions')
    op.drop_table('storytags')
    op.drop_table('story_storytags')
    op.drop_table('comments')
    op.drop_table('tasks')
    op.drop_table('projects')
    op.drop_table('milestones')
    op.drop_table('stories')
    op.drop_table('permissions')
    op.drop_table('teams')
    op.drop_table('users')
    op.drop_table('project_groups')
    op.drop_table('branches')
    op.drop_table('authorizationcodes')
    op.drop_table('refreshtokens')
    op.drop_table('accesstokens')
    op.drop_table('subscriptions')
    op.drop_table('subscription_events')
    op.drop_table('user_preferences')
    op.drop_table('branches')
    op.drop_table('milestones')
    op.drop_table('story_types')
    op.drop_table('may_mutate_to')

    # Need to explicitly delete enums during migrations for Postgres
    enums = _define_enums()
    for enum in enums.values():
        enum.drop(op.get_bind())
