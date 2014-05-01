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

"""Remove story priorities, add task priorities.

Revision ID: 017
Revises: 016
Create Date: 2014-04-15 17:16:07.368141

"""

# revision identifiers, used by Alembic.
revision = '018'
down_revision = '017'

from alembic import op
import sqlalchemy as sa


def _define_enums():
    task_priority = sa.Enum(
        'low', 'medium', 'high',
        name='task_priority')

    return {
        'task_priority': task_priority
    }


def upgrade(active_plugins=None, options=None):
    enums = _define_enums()

    op.add_column('tasks',
                  sa.Column('priority', enums['task_priority'], nullable=True))


def downgrade(active_plugins=None, options=None):
    op.drop_column('tasks', 'priority')
