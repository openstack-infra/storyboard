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

"""This migration adds new column for branch id and merge all tasks to branch
'master' in corresponding project.

Revision ID: 037
Revises: 036
Create Date: 2015-01-27 13:17:34.622503

"""

# revision identifiers, used by Alembic.

revision = '037'
down_revision = '036'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql.expression import table

MYSQL_ENGINE = 'InnoDB'
MYSQL_CHARSET = 'utf8'


def upgrade(active_plugins=None, options=None):
    op.add_column(
        'tasks',
        sa.Column('branch_id', sa.Integer(), nullable=True)
    )

    bind = op.get_bind()

    branches = list(bind.execute(
        sa.select(columns=['id', 'name', 'project_id'],
                  from_obj=sa.Table('branches', sa.MetaData()))))

    projects = list(bind.execute(
        sa.select(columns=['id'], from_obj=sa.Table('projects',
                                                    sa.MetaData()))))
    branch_dict = {}

    for branch in branches:
        branch_dict[(branch['project_id'], branch['name'])] = branch['id']

    tasks_table = table(
        'tasks',
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('branch_id', sa.Integer(), nullable=True)
    )

    for project in projects:
        bind.execute(
            tasks_table.update().
            where(tasks_table.c.project_id == project['id']).
            values(branch_id=branch_dict[(project['id'], "master")])
        )


def downgrade(active_plugins=None, options=None):
    op.drop_column('tasks', 'branch_id')
