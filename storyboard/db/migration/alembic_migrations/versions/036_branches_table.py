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

"""This migration adds new table for branches and for all projects in database
adds branch with name 'master'.

Revision ID: 036
Revises: 035
Create Date: 2015-01-26 13:03:34.622503

"""

# revision identifiers, used by Alembic.

revision = '036'
down_revision = '035'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql.expression import table

MYSQL_ENGINE = 'InnoDB'
MYSQL_CHARSET = 'utf8'


def upgrade(active_plugins=None, options=None):
    op.create_table(
        'branches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('expired', sa.Boolean(), default=False, nullable=True),
        sa.Column('expiration_date', sa.DateTime(), default=None,
                  nullable=True),
        sa.Column('autocreated', sa.Boolean(), default=False, nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', 'project_id', name="branch_un_constr"),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )

    bind = op.get_bind()

    projects = list(bind.execute(
        sa.select(columns=['id', 'created_at', 'updated_at'],
                  from_obj=sa.Table('projects', sa.MetaData()))))

    branches_table = table(
        'branches',
        sa.Column('name', sa.String(100), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('expired', sa.Boolean(), default=False),
        sa.Column('expiration_date', sa.DateTime(), default=None),
        sa.Column('autocreated', sa.Boolean(), default=False),
    )

    for project in projects:
        bind.execute(branches_table.insert().values(
            name="master",
            project_id=project['id'],
            created_at=project['created_at'],
            updated_at=project['updated_at']
        ))


def downgrade(active_plugins=None, options=None):
    op.drop_table('branches')
