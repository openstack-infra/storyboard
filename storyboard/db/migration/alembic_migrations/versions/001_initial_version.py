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
import sqlalchemy as sa

MYSQL_ENGINE = 'InnoDB'
MYSQL_CHARSET = 'utf8'


def _define_enums():
    branch_status = sa.Enum(
        'master', 'release', 'stable', 'unsupported',
        name='branch_status')

    storyboard_priority = sa.Enum(
        'Undefined', 'Low', 'Medium', 'High', 'Critical',
        name='priority')

    task_status = sa.Enum(
        'Todo', 'In review', 'Landed',
        name='task_status')

    return {
        'branch_status': branch_status,
        'storyboard_priority': storyboard_priority,
        'task_status': task_status
    }


def upgrade(active_plugins=None, options=None):
    enums = _define_enums()

    op.create_table(
        'branches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('name', sa.String(length=50), nullable=True),
        sa.Column('status', enums['branch_status'], nullable=True),
        sa.Column('release_date', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uniq_branch_name'),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )
    op.create_table(
        'project_groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('name', sa.String(length=50), nullable=True),
        sa.Column('title', sa.Unicode(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uniq_group_name'),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('username', sa.Unicode(length=30), nullable=True),
        sa.Column('first_name', sa.Unicode(length=30), nullable=True),
        sa.Column('last_name', sa.Unicode(length=30), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('password', sa.UnicodeText(), nullable=True),
        sa.Column('is_staff', sa.Boolean(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=True),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='uniq_user_email'),
        sa.UniqueConstraint('username', name='uniq_user_username'),
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
        sa.Column('title', sa.Unicode(length=100), nullable=True),
        sa.Column('description', sa.UnicodeText(), nullable=True),
        sa.Column('is_bug', sa.Boolean(), nullable=True),
        sa.Column('priority', enums['storyboard_priority'], nullable=True),
        sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )
    op.create_table(
        'milestones',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('name', sa.String(length=50), nullable=True),
        sa.Column('branch_id', sa.Integer(), nullable=True),
        sa.Column('released', sa.Boolean(), nullable=True),
        sa.Column('undefined', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uniq_milestone_name'),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('name', sa.String(length=50), nullable=True),
        sa.Column('description', sa.Unicode(length=100), nullable=True),
        sa.Column('team_id', sa.Integer(), nullable=True),
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
        sa.Column('title', sa.Unicode(length=100), nullable=True),
        sa.Column('status', enums['task_status'], nullable=True),
        sa.Column('story_id', sa.Integer(), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('assignee_id', sa.Integer(), nullable=True),
        sa.Column('milestone_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['assignee_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['milestone_id'], ['milestones.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['story_id'], ['stories.id'], ),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )
    op.create_table(
        'comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('action', sa.String(length=150), nullable=True),
        sa.Column('comment_type', sa.String(length=20), nullable=True),
        sa.Column('content', sa.UnicodeText(), nullable=True),
        sa.Column('story_id', sa.Integer(), nullable=True),
        sa.Column('author_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['story_id'], ['stories.id'], ),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )
    op.create_table(
        'storytags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('name', sa.String(length=20), nullable=True),
        sa.Column('story_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['story_id'], ['stories.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uniq_story_tags_name'),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )


def downgrade(active_plugins=None, options=None):
    # be careful with the order, keep FKs in mind
    op.drop_table('project_group_mapping')
    op.drop_table('team_membership')
    op.drop_table('team_permissions')
    op.drop_table('user_permissions')
    op.drop_table('storytags')
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

    # Need to explicitly delete enums during migrations for Postgres
    enums = _define_enums()
    for enum in enums.values():
        enum.drop(op.get_bind())
