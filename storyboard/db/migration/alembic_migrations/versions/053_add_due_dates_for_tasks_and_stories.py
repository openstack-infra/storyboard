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

"""Add due dates for tasks and stories

Revision ID: 053
Revises: 052
Create Date: 2016-02-04 11:27:55.607256

"""

# revision identifiers, used by Alembic.
revision = '053'
down_revision = '052'


from alembic import op
import sqlalchemy as sa

from storyboard.db.decorators import UTCDateTime


def upgrade(active_plugins=None, options=None):
    op.create_table(
        'due_dates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', UTCDateTime(), nullable=True),
        sa.Column('updated_at', UTCDateTime(), nullable=True),
        sa.Column('name', sa.Unicode(length=100), nullable=True),
        sa.Column('date', UTCDateTime(), nullable=True),
        sa.Column('private', sa.Boolean(), nullable=True),
        sa.Column('creator_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'due_date_permissions',
        sa.Column('due_date_id', sa.Integer(), nullable=True),
        sa.Column('permission_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['due_date_id'], ['due_dates.id'], ),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], )
    )
    op.create_table(
        'story_due_dates',
        sa.Column('story_id', sa.Integer(), nullable=True),
        sa.Column('due_date_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['due_date_id'], ['due_dates.id'], ),
        sa.ForeignKeyConstraint(['story_id'], ['stories.id'], )
    )
    op.create_table(
        'board_due_dates',
        sa.Column('board_id', sa.Integer(), nullable=True),
        sa.Column('due_date_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['board_id'], ['boards.id'], ),
        sa.ForeignKeyConstraint(['due_date_id'], ['due_dates.id'], )
    )
    op.create_table(
        'worklist_due_dates',
        sa.Column('worklist_id', sa.Integer(), nullable=True),
        sa.Column('due_date_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['due_date_id'], ['due_dates.id'], ),
        sa.ForeignKeyConstraint(['worklist_id'], ['worklists.id'], )
    )
    op.create_table(
        'task_due_dates',
        sa.Column('task_id', sa.Integer(), nullable=True),
        sa.Column('due_date_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['due_date_id'], ['due_dates.id'], ),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], )
    )
    op.add_column(
        'worklist_items',
        sa.Column('display_due_date', sa.Integer(), nullable=True)
    )
    dialect = op.get_bind().engine.dialect
    if dialect.supports_alter:
        op.create_foreign_key(
            None, 'worklist_items', 'due_dates', ['display_due_date'], ['id'])


def downgrade(active_plugins=None, options=None):
    op.drop_constraint(None, 'worklist_items', type_='foreignkey')
    op.drop_column('worklist_items', 'display_due_date')
    op.drop_table('task_due_dates')
    op.drop_table('worklist_due_dates')
    op.drop_table('board_due_dates')
    op.drop_table('story_due_dates')
    op.drop_table('due_date_permissions')
    op.drop_table('due_dates')
