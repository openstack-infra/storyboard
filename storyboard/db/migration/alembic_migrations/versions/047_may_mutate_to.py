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

"""This migration adds may_mutate_to table.

Revision ID: 047
Revises: 046
Create Date: 2015-03-10 17:47:34.395641

"""

# revision identifiers, used by Alembic.

revision = '047'
down_revision = '046'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql.expression import table

MYSQL_ENGINE = 'InnoDB'
MYSQL_CHARSET = 'utf8'


def upgrade(active_plugins=None, options=None):
    op.create_table(
        'may_mutate_to',
        sa.Column('story_type_id_from', sa.Integer(), nullable=False),
        sa.Column('story_type_id_to', sa.Integer(), nullable=False),
        sa.UniqueConstraint('story_type_id_from',
                            'story_type_id_to',
                            name="mutate_un_constr"),
        sa.PrimaryKeyConstraint(),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )

    bind = op.get_bind()

    story_types_table = table(
        'may_mutate_to',
        sa.Column('story_type_id_from', sa.Integer(), nullable=False),
        sa.Column('story_type_id_to', sa.Integer(), nullable=False),
    )

    bind.execute(story_types_table.insert().values(
        story_type_id_from=1,
        story_type_id_to=4
    ))

    bind.execute(story_types_table.insert().values(
        story_type_id_from=1,
        story_type_id_to=2
    ))

    bind.execute(story_types_table.insert().values(
        story_type_id_from=2,
        story_type_id_to=1
    ))

    bind.execute(story_types_table.insert().values(
        story_type_id_from=3,
        story_type_id_to=4
    ))

    bind.execute(story_types_table.insert().values(
        story_type_id_from=3,
        story_type_id_to=1
    ))

    bind.execute(story_types_table.insert().values(
        story_type_id_from=4,
        story_type_id_to=1
    ))


def downgrade(active_plugins=None, options=None):
    op.drop_table('may_mutate_to')
