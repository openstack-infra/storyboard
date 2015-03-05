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

"""This migration adds story types table.

Revision ID: 044
Revises: 043
Create Date: 2015-03-10 14:52:55.783625

"""

# revision identifiers, used by Alembic.

revision = '044'
down_revision = '043'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql.expression import table

MYSQL_ENGINE = 'InnoDB'
MYSQL_CHARSET = 'utf8'


def upgrade(active_plugins=None, options=None):
    op.create_table(
        'story_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('name', sa.String(50), nullable=True),
        sa.Column('icon', sa.String(50), nullable=True),
        sa.Column('restricted', sa.Boolean(), default=False),
        sa.Column('private', sa.Boolean(), default=False),
        sa.Column('visible', sa.Boolean(), default=True),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )

    bind = op.get_bind()

    story_types_table = table(
        'story_types',
        sa.Column('name', sa.String(50), nullable=True),
        sa.Column('icon', sa.String(50), nullable=True),
        sa.Column('restricted', sa.Boolean(), default=False),
        sa.Column('private', sa.Boolean(), default=False),
        sa.Column('visible', sa.Boolean(), default=True),
    )

    bind.execute(story_types_table.insert().values(
        name='bug',
        icon='fa-bug'
    ))

    bind.execute(story_types_table.insert().values(
        name='feature',
        icon='fa-lightbulb-o',
        restricted=True
    ))

    bind.execute(story_types_table.insert().values(
        name='private_vulnerability',
        icon='fa-lock',
        private=True
    ))

    bind.execute(story_types_table.insert().values(
        name='public_vulnerability',
        icon='fa-bomb',
        visible=False
    ))


def downgrade(active_plugins=None, options=None):
    op.drop_table('story_types')
