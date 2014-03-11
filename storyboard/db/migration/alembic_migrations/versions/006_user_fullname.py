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

"""Converts the user object to use full_name

Revision ID: 56bda170aa42
Revises: 128470dcd02f
Create Date: 2014-03-11 10:45:59.122062

"""

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql.expression import column
from sqlalchemy.sql.expression import table


def upgrade(active_plugins=None, options=None):
    op.add_column(
        'users',
        sa.Column('full_name', sa.Unicode(255), nullable=True)
    )

    users = table(
        'users',
        column('first_name', sa.Unicode(30)),
        column('last_name', sa.Unicode(30)),
        column('full_name', sa.Unicode(255))
    )
    users.update().values(
        {'full_name': column('first_name') + op.inline_literal(' ') + column(
            'last_name')})

    op.drop_column('users', 'first_name')
    op.drop_column('users', 'last_name')


def downgrade(active_plugins=None, options=None):
    op.add_column(
        'users',
        sa.Column('first_name', sa.Unicode(length=30), nullable=True)
    )
    op.add_column(
        'users',
        sa.Column('last_name', sa.Unicode(length=30), nullable=True)
    )
    op.drop_column('users', 'full_name')
