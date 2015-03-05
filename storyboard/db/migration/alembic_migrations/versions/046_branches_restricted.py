# Copyright (c) 2015 Mirantis Inc.
#
#  Licensed under the Apache License, Version 2.0 (the "License"); you may
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

"""This migration adds restricted field to branches table and sets this field
to True in branches with name 'master'.

Revision ID: 046
Revises: 045
Create Date: 2015-03-10 15:23:54.723124

"""

# revision identifiers, used by Alembic.

revision = '046'
down_revision = '045'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql.expression import table

MYSQL_ENGINE = 'InnoDB'
MYSQL_CHARSET = 'utf8'


def upgrade(active_plugins=None, options=None):
    op.add_column(
        'branches',
        sa.Column('restricted', sa.Boolean(), default=False)
    )

    bind = op.get_bind()

    branches_table = table(
        'branches',
        sa.Column('name', sa.String(100), nullable=True),
        sa.Column('restricted', sa.Boolean(), default=False)
    )

    bind.execute(
        branches_table.update().where(
            branches_table.c.name != 'master'
        ).values(restricted=False)
    )

    bind.execute(
        branches_table.update().where(
            branches_table.c.name == 'master'
        ).values(restricted=True)
    )


def downgrade(active_plugins=None, options=None):
    op.drop_column('branches', 'restricted')
