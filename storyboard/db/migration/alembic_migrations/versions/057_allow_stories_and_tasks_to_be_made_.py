# Copyright 2016 Codethink Ltd
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
#

"""Allow stories and tasks to be made private

This also allows worklist_items.list_id to be NULL, to facilitate
filtering of the relationship between worklists and their items
using dynamic loading.

This is needed because moving items temporarily causes them to be in
no list.

Revision ID: 057
Revises: 056
Create Date: 2016-04-27 15:45:51.646556

"""

# revision identifiers, used by Alembic.
revision = '057'
down_revision = '056'


from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


def upgrade(active_plugins=None, options=None):
    op.create_table(
        'story_permissions',
        sa.Column('story_id', sa.Integer(), nullable=True),
        sa.Column('permission_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ),
        sa.ForeignKeyConstraint(['story_id'], ['stories.id'], )
    )
    dialect = op.get_bind().engine.dialect
    if dialect.name == 'sqlite':
        col = sa.Column('private', sa.Boolean(), default=False)
    else:
        col = sa.Column('private', sa.Boolean(), default=False, nullable=False)
    op.add_column(u'stories', col)
    if dialect.supports_alter:
        op.alter_column('worklist_items', 'list_id',
                        existing_type=mysql.INTEGER(display_width=11),
                        nullable=True)


def downgrade(active_plugins=None, options=None):
    op.drop_constraint(
        u'worklist_items_ibfk_1', 'worklist_items', type_='foreignkey')
    op.alter_column('worklist_items', 'list_id',
               existing_type=mysql.INTEGER(display_width=11),
               nullable=False)
    op.create_foreign_key(u'worklist_items_ibfk_1', 'worklist_items',
                          'worklists', ['list_id'], ['id'])
    op.drop_column(u'stories', 'private')
    op.drop_table('story_permissions')
