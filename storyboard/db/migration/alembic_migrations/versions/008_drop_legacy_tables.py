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

"""Remove Branch, Milestone tables

Revision ID: 008
Revises: 007
Create Date: 2014-03-19 15:00:39.149963

"""

# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'


from alembic import op
import sqlalchemy as sa

MYSQL_ENGINE = 'InnoDB'
MYSQL_CHARSET = 'utf8'


def _define_enums():
    branch_status = sa.Enum(
        'master', 'release', 'stable', 'unsupported',
        name='branch_status')

    return {
        'branch_status': branch_status
    }


def upgrade(active_plugins=None, options=None):
    op.drop_constraint('tasks_ibfk_2',
                       'tasks', type_='foreignkey')
    op.drop_column('tasks', 'milestone_id')
    op.drop_table('milestones')
    op.drop_table('branches')

    # Need to explicitly delete enums during migrations for Postgres
    enums = _define_enums()
    for enum in enums.values():
        enum.drop(op.get_bind())


def downgrade(active_plugins=None, options=None):
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
    op.add_column('tasks', sa.Column('milestone_id',
                                     sa.Integer(),
                                     nullable=True))
    op.create_foreign_key('tasks_ibfk_2', 'tasks',
                          'milestones', ['milestone_id'], ['id'])
