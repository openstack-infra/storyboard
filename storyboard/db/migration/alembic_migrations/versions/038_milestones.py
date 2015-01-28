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

"""This migration adds milestones table.

Revision ID: 038
Revises: 037
Create Date: 2015-01-28 15:26:34.622503

"""

# revision identifiers, used by Alembic.

revision = '038'
down_revision = '037'

from alembic import op
import sqlalchemy as sa

MYSQL_ENGINE = 'InnoDB'
MYSQL_CHARSET = 'utf8'


def upgrade(active_plugins=None, options=None):
    op.create_table(
        'milestones',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=True),
        sa.Column('branch_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('expired', sa.Boolean(), default=False, nullable=True),
        sa.Column('expiration_date', sa.DateTime(), default=None),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', 'branch_id', name="milestone_un_constr"),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )


def downgrade(active_plugins=None, options=None):
    op.drop_table('milestones')
