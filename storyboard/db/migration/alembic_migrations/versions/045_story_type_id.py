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

"""This migration adds story type id to stories table and sets story type id
to 1 (bugs) in all stories.

Revision ID: 045
Revises: 044
Create Date: 2015-03-10 15:23:54.723124

"""

# revision identifiers, used by Alembic.

revision = '045'
down_revision = '044'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql.expression import table

MYSQL_ENGINE = 'InnoDB'
MYSQL_CHARSET = 'utf8'


def upgrade(active_plugins=None, options=None):
    op.add_column(
        'stories',
        sa.Column('story_type_id', sa.Integer(), default=1)
    )

    bind = op.get_bind()

    stories_table = table(
        'stories',
        sa.Column('story_type_id', sa.Integer(), default=1)
    )

    bind.execute(stories_table.update().values(story_type_id=1))


def downgrade(active_plugins=None, options=None):
    op.drop_column('stories', 'story_type_id')
