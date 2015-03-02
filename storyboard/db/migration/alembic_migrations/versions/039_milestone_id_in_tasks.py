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

"""This migration adds new column for milestone id.

Revision ID: 039
Revises: 038
Create Date: 2015-01-27 13:17:34.622503

"""

# revision identifiers, used by Alembic.

revision = '039'
down_revision = '038'

from alembic import op
import sqlalchemy as sa


def upgrade(active_plugins=None, options=None):
    op.add_column(
        'tasks',
        sa.Column('milestone_id', sa.Integer(), nullable=True)
    )


def downgrade(active_plugins=None, options=None):
    op.drop_column('tasks', 'milestone_id')
