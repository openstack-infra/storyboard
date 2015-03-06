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

"""This migration fix project_id and branch_id fields in tasks. All tasks
without project id now are assigned to project with the smallest id. All tasks
without branch_id now assigned to masted branch of matching project.

Revision ID: 043
Revises: 042
Create Date: 2015-03-24 13:11:22

"""

# revision identifiers, used by Alembic.

revision = '043'
down_revision = '042'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql.expression import table

MYSQL_ENGINE = 'InnoDB'
MYSQL_CHARSET = 'utf8'


def upgrade(active_plugins=None, options=None):
    bind = op.get_bind()

    branches = list(bind.execute(
        sa.select(columns=['id', 'name', 'project_id'],
                  from_obj=sa.Table('branches', sa.MetaData()))))

    projects = list(bind.execute(
        sa.select(columns=['id'], from_obj=sa.Table('projects',
                                                    sa.MetaData()))))
    if len(projects) > 0:
        branch_dict = {}

        for branch in branches:
            branch_dict[(branch['project_id'], branch['name'])] = branch['id']

        tasks_table = table(
            'tasks',
            sa.Column('project_id', sa.Integer(), nullable=True),
            sa.Column('branch_id', sa.Integer(), nullable=True),
        )

        bind.execute(tasks_table.update().
                     where(tasks_table.c.project_id.is_(None)).
                     values(project_id=projects[0].id))

        for project in projects:
            bind.execute(
                tasks_table.update().
                where(tasks_table.c.project_id == project['id']).
                values(branch_id=branch_dict[(project['id'], "master")])
            )


def downgrade(active_plugins=None, options=None):
    pass
