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

"""This migration converts our many-to-many mapping among auth tokens into
a one-to-one relationship.

Revision ID: 048
Revises: 047
Create Date: 2015-04-12 18:03:23

"""

# revision identifiers, used by Alembic.

revision = '048'
down_revision = '047'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql.expression import table

MYSQL_ENGINE = 'InnoDB'
MYSQL_CHARSET = 'utf8'


def upgrade(active_plugins=None, options=None):
    op.add_column('refreshtokens', sa.Column('access_token_id',
                                             sa.Integer(),
                                             nullable=False))
    op.drop_table('access_refresh_tokens')

    # Delete all refresh and access tokens, as the relationship is no longer
    # valid.
    bind = op.get_bind()

    refresh_table = table(
        'refreshtokens'
    )
    access_table = table(
        'accesstokens'
    )

    bind.execute(refresh_table.delete())
    bind.execute(access_table.delete())


def downgrade(active_plugins=None, options=None):
    op.create_table('access_refresh_tokens',
                    sa.Column('access_token_id', sa.Integer(), nullable=False),
                    sa.Column('refresh_token_id', sa.Integer(),
                              nullable=False),
                    mysql_engine=MYSQL_ENGINE,
                    mysql_charset=MYSQL_CHARSET
                    )
    op.drop_column(u'refreshtokens', u'access_token_id')
