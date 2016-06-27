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

"""Add a table for comment history

Revision ID: 059
Revises: 058
Create Date: 2016-06-21 14:00:20.515139

"""

# revision identifiers, used by Alembic.
revision = '059'
down_revision = '058'


from alembic import op
import sqlalchemy as sa

from storyboard.db.decorators import UTCDateTime
from storyboard.db.models import MYSQL_MEDIUM_TEXT


def upgrade(active_plugins=None, options=None):
    op.create_table(
        'comments_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', UTCDateTime(), nullable=True),
        sa.Column('updated_at', UTCDateTime(), nullable=True),
        sa.Column('content', MYSQL_MEDIUM_TEXT, nullable=True),
        sa.Column('comment_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['comment_id'], ['comments.id'],
                                name='fk_comment_id'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade(active_plugins=None, options=None):
    op.drop_table('comments_history')
