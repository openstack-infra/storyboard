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

"""deletion states

Revision ID: 003
Revises: 002
Create Date: 2014-03-03 16:08:12.584302

"""

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'

from alembic import op
from sqlalchemy import Boolean
from sqlalchemy import Column


def upgrade(active_plugins=None, options=None):
    op.add_column('projects',
                  Column('is_active', Boolean(), default=True))
    op.add_column('stories',
                  Column('is_active', Boolean(), default=True))
    op.add_column('tasks',
                  Column('is_active', Boolean(), default=True))


def downgrade(active_plugins=None, options=None):
    op.drop_column('projects', 'is_active')
    op.drop_column('stories', 'is_active')
    op.drop_column('tasks', 'is_active')
