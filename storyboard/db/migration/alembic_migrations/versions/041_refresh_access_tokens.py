# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#

"""This migration creates new table for relations between access and refresh
tokens.

Revision ID: 041
Revises: 040
Create Date: 2015-02-18 18:03:23

"""

# revision identifiers, used by Alembic.

revision = '041'
down_revision = '040'

from alembic import op
import sqlalchemy as sa

MYSQL_ENGINE = 'InnoDB'
MYSQL_CHARSET = 'utf8'


def upgrade(active_plugins=None, options=None):
    op.create_table('access_refresh_tokens',
                    sa.Column('access_token_id', sa.Integer(), nullable=False),
                    sa.Column('refresh_token_id', sa.Integer(),
                              nullable=False),
                    mysql_engine=MYSQL_ENGINE,
                    mysql_charset=MYSQL_CHARSET
                    )
    op.drop_column(u'refreshtokens', u'access_token_id')


def downgrade(active_plugins=None, options=None):
    op.add_column('refreshtokens', sa.Column('access_token_id',
                                             sa.Integer(),
                                             nullable=False))
    op.drop_table('access_refresh_tokens')
