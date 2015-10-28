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

"""Use filters with multiple criteria for automatic worklists

Revision ID: 056
Revises: 055
Create Date: 2016-03-04 13:31:01.600372

"""

# revision identifiers, used by Alembic.
revision = '056'
down_revision = '055'


from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

import storyboard


def upgrade(active_plugins=None, options=None):
    op.create_table(
        'worklist_filters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', storyboard.db.decorators.UTCDateTime(),
                  nullable=True),
        sa.Column('updated_at', storyboard.db.decorators.UTCDateTime(),
                  nullable=True),
        sa.Column('type', sa.Unicode(length=50), nullable=False),
        sa.Column('list_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['list_id'], ['worklists.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'filter_criteria',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', storyboard.db.decorators.UTCDateTime(),
                  nullable=True),
        sa.Column('updated_at', storyboard.db.decorators.UTCDateTime(),
                  nullable=True),
        sa.Column('title', sa.Unicode(length=100), nullable=False),
        sa.Column('value', sa.Unicode(length=50), nullable=False),
        sa.Column('field', sa.Unicode(length=50), nullable=False),
        sa.Column('negative', sa.Boolean(), nullable=False),
        sa.Column('filter_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['filter_id'], ['worklist_filters.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('worklist_criteria')


def downgrade(active_plugins=None, options=None):
    op.create_table(
        'worklist_criteria',
        sa.Column('id', mysql.INTEGER(display_width=11), nullable=False),
        sa.Column('created_at', mysql.DATETIME(), nullable=True),
        sa.Column('updated_at', mysql.DATETIME(), nullable=True),
        sa.Column('title', mysql.VARCHAR(length=100), nullable=False),
        sa.Column('list_id', mysql.INTEGER(display_width=11),
                  autoincrement=False, nullable=False),
        sa.Column('value', mysql.VARCHAR(length=50), nullable=False),
        sa.Column('field', mysql.VARCHAR(length=50), nullable=False),
        sa.ForeignKeyConstraint(['list_id'], [u'worklists.id'],
                                name=u'worklist_criteria_ibfk_1'),
        sa.PrimaryKeyConstraint('id'),
        mysql_default_charset=u'latin1',
        mysql_engine=u'InnoDB'
    )
    op.drop_table('filter_criteria')
    op.drop_table('worklist_filters')
