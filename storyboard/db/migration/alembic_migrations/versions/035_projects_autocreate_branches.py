# Copyright (c) 2015 Mirantis Inc.
#
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

"""This migration adds new column for autocreate branches and makes it 'false'
in all projects in database.

Revision ID: 035
Revises: 034
Create Date: 2015-01-26 13:00:02.622503

"""

# revision identifiers, used by Alembic.

revision = '035'
down_revision = '034'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql.expression import table


def upgrade(active_plugins=None, options=None):
    op.add_column('projects', sa.Column('autocreate_branches',
                                        sa.Boolean(),
                                        default=False))

    projects_table = table(
        'projects',
        sa.Column('autocreate_branches', sa.Boolean(), nullable=True)
    )

    bind = op.get_bind()
    bind.execute(projects_table.update().
                 values(autocreate_branches=False))


def downgrade(active_plugins=None, options=None):
    op.drop_column('projects', 'autocreate_branches')
