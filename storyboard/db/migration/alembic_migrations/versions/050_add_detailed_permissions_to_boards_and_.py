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

"""Add detailed permissions to boards and worklists

Revision ID: 050
Revises: 049
Create Date: 2015-10-09 10:25:47.338906

"""

# revision identifiers, used by Alembic.
revision = '050'
down_revision = '049'


from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from storyboard.db.api import base as api_base
from storyboard.db.api import boards
from storyboard.db.api import worklists
from storyboard.db import models


def upgrade(active_plugins=None, options=None):
    op.create_table('board_permissions',
        sa.Column('board_id', sa.Integer(), nullable=True),
        sa.Column('permission_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['board_id'], ['boards.id'], ),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], )
    )
    op.create_table('worklist_permissions',
        sa.Column('worklist_id', sa.Integer(), nullable=True),
        sa.Column('permission_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ),
        sa.ForeignKeyConstraint(['worklist_id'], ['worklists.id'], )
    )

    session = api_base.get_session(in_request=False)
    for board in boards.get_all(session=session):
        edit_permission = {
            'name': 'edit_board_%d' % board.id,
            'codename': 'edit_board',
            'users': [board.creator_id]
        }
        move_permission = {
            'name': 'move_cards_%d' % board.id,
            'codename': 'move_cards',
            'users': []
        }
        print('Creating permissions for Board with id: %d' % board.id)
        boards.create_permission(board.id, edit_permission, session=session)
        boards.create_permission(board.id, move_permission, session=session)

    for worklist in worklists.get_all(session=session):
        edit_permission = {
            'name': 'edit_worklist_%d' % worklist.id,
            'codename': 'edit_worklist',
            'users': [worklist.creator_id]
        }
        move_permission = {
            'name': 'move_items_%d' % worklist.id,
            'codename': 'move_items',
            'users': []
        }
        print('Creating permissions for Worklist with id: %d' % worklist.id)
        worklists.create_permission(
            worklist.id, edit_permission, session=session)
        worklists.create_permission(
            worklist.id, move_permission, session=session)
        session.flush()

    dialect = op.get_bind().engine.dialect
    if dialect.supports_alter:
        op.drop_constraint(u'boards_ibfk_2', 'boards', type_='foreignkey')
        op.drop_column(u'boards', 'permission_id')
        op.drop_constraint(u'worklists_ibfk_2', 'worklists',
                           type_='foreignkey')
        op.drop_column(u'worklists', 'permission_id')


def downgrade(active_plugins=None, options=None):
    op.add_column(u'worklists', sa.Column('permission_id',
                  mysql.INTEGER(display_width=11), autoincrement=False,
                  nullable=True))
    op.create_foreign_key(u'worklists_ibfk_2', 'worklists', 'permissions',
                          ['permission_id'], ['id'])
    op.add_column(u'boards', sa.Column('permission_id',
                  mysql.INTEGER(display_width=11), autoincrement=False,
                  nullable=True))
    op.create_foreign_key(u'boards_ibfk_2', 'boards', 'permissions',
                          ['permission_id'], ['id'])

    session = api_base.get_session(in_request=False)
    to_delete = []
    for board in boards.get_all(session=session):
        for permission in board.permissions:
            to_delete.append(permission)

    for worklist in worklists.get_all(session=session):
        for permission in worklist.permissions:
            to_delete.append(permission)

    op.drop_table('worklist_permissions')
    op.drop_table('board_permissions')

    for permission in to_delete:
        api_base.entity_hard_delete(
            models.Permission, permission.id, session=session)
