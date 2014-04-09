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

"""Update task states

Revision ID: 011
Revises: 010
Create Date: 2014-03-21 17:44:51.248232

"""

# revision identifiers, used by Alembic.
revision = '012'
down_revision = '011'

from alembic import op
import sqlalchemy as sa

MYSQL_ENGINE = 'InnoDB'
MYSQL_CHARSET = 'utf8'


def _define_enums():
    task_status_old = sa.Enum(
        'Todo', 'In review', 'Landed',
        name='task_status')

    task_status_new = sa.Enum(
        'todo', 'inprogress', 'invalid', 'review', 'merged',
        name='task_status')

    return {
        'task_status_old': task_status_old,
        'task_status_new': task_status_new
    }


def upgrade(active_plugins=None, options=None):
    enums = _define_enums()

    op.drop_column('tasks', 'status')
    op.add_column('tasks', sa.Column('status',
                                     enums['task_status_new'],
                                     nullable=True))


def downgrade(active_plugins=None, options=None):
    enums = _define_enums()

    op.drop_column('tasks', 'status')
    op.add_column('tasks', sa.Column('status',
                                     enums['task_status_old'],
                                     nullable=True))
