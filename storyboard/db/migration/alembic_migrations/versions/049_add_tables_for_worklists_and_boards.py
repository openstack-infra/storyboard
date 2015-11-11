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

"""Add tables for worklists and boards

Revision ID: 049
Revises: 048
Create Date: 2015-08-17 12:17:35.629353

"""

# revision identifiers, used by Alembic.
revision = '049'
down_revision = '048'


from alembic import op
import sqlalchemy as sa

import storyboard


def upgrade(active_plugins=None, options=None):
    op.create_table('worklists',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at',
            storyboard.db.decorators.UTCDateTime(), nullable=True),
        sa.Column('updated_at',
            storyboard.db.decorators.UTCDateTime(), nullable=True),
        sa.Column('title', sa.Unicode(length=100), nullable=True),
        sa.Column('creator_id', sa.Integer(), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('permission_id', sa.Integer(), nullable=True),
        sa.Column('private', sa.Boolean(), nullable=True),
        sa.Column('archived', sa.Boolean(), nullable=True),
        sa.Column('automatic', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('boards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at',
            storyboard.db.decorators.UTCDateTime(), nullable=True),
        sa.Column('updated_at',
            storyboard.db.decorators.UTCDateTime(), nullable=True),
        sa.Column('title', sa.Unicode(length=100), nullable=False),
        sa.Column('description', sa.UnicodeText(), nullable=True),
        sa.Column('creator_id', sa.Integer(), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('permission_id', sa.Integer(), nullable=True),
        sa.Column('private', sa.Boolean(), nullable=True),
        sa.Column('archived', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('worklist_criteria',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at',
            storyboard.db.decorators.UTCDateTime(), nullable=True),
        sa.Column('updated_at',
            storyboard.db.decorators.UTCDateTime(), nullable=True),
        sa.Column('title', sa.Unicode(length=100), nullable=True),
        sa.Column('list_id', sa.Integer(), nullable=False),
        sa.Column('value', sa.Unicode(length=50), nullable=False),
        sa.Column('field', sa.Unicode(length=50), nullable=False),
        sa.ForeignKeyConstraint(['list_id'], ['worklists.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('worklist_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at',
            storyboard.db.decorators.UTCDateTime(), nullable=True),
        sa.Column('updated_at',
            storyboard.db.decorators.UTCDateTime(), nullable=True),
        sa.Column('list_id', sa.Integer(), nullable=False),
        sa.Column('list_position', sa.Integer(), nullable=False),
        sa.Column('item_type', sa.Enum('story', 'task'), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['list_id'], ['worklists.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('board_worklists',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at',
            storyboard.db.decorators.UTCDateTime(), nullable=True),
        sa.Column('updated_at',
            storyboard.db.decorators.UTCDateTime(), nullable=True),
        sa.Column('board_id', sa.Integer(), nullable=False),
        sa.Column('list_id', sa.Integer(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['board_id'], ['boards.id'], ),
        sa.ForeignKeyConstraint(['list_id'], ['worklists.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade(active_plugins=None, options=None):
    op.drop_table('board_worklists')
    op.drop_table('worklist_items')
    op.drop_table('worklist_criteria')
    op.drop_table('boards')
    op.drop_table('worklists')
