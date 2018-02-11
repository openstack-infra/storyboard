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

"""Allow timeline events to be related to boards and worklists

Revision ID: 060
Revises: 059
Create Date: 2016-07-14 15:05:12.369072

"""

# revision identifiers, used by Alembic.
revision = '060'
down_revision = '059'


from alembic import op
import sqlalchemy as sa


def upgrade(active_plugins=None, options=None):
    op.add_column(
        'events', sa.Column('board_id', sa.Integer(), nullable=True))
    op.add_column(
        'events', sa.Column('worklist_id', sa.Integer(), nullable=True))
    dialect = op.get_bind().engine.dialect
    if dialect.supports_alter:
        op.create_foreign_key(
            'fk_event_worklist', 'events', 'worklists',
            ['worklist_id'], ['id'])
        op.create_foreign_key(
            'fk_event_board', 'events', 'boards', ['board_id'], ['id'])


def downgrade(active_plugins=None, options=None):
    op.drop_constraint('fk_event_worklist', 'events', type_='foreignkey')
    op.drop_constraint('fk_event_board', 'events', type_='foreignkey')
    op.drop_column('events', 'worklist_id')
    op.drop_column('events', 'board_id')
