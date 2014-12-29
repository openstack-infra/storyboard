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

"""This migration resize fields in project_groups, stories ans tasks

Revision ID: 031
Revises: 030
Create Date: 2014-12-24 01:00:00

"""

# revision identifiers, used by Alembic.
revision = '031'
down_revision = '030'

import sqlalchemy as sa

from alembic import op


def upgrade(active_plugins=None, options=None):

    op.alter_column('project_groups', 'title', type_=sa.Unicode(255))
    op.alter_column('stories', 'title', type_=sa.Unicode(255))
    op.alter_column('tasks', 'title', type_=sa.Unicode(255))


def downgrade(active_plugins=None, options=None):
    op.alter_column('project_groups', 'title', type_=sa.Unicode(100))
    op.alter_column('stories', 'title', type_=sa.Unicode(100))
    op.alter_column('tasks', 'title', type_=sa.Unicode(100))
