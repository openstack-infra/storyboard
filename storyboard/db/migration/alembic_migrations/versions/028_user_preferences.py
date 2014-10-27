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

"""Adds a user_preferences table.

Revision ID: 028
Revises: 027
Create Date: 2014-09-14 01:00:00

"""

# revision identifiers, used by Alembic.
revision = '028'
down_revision = '027'

from alembic import op
import sqlalchemy as sa

pref_type_enum = sa.Enum('string', 'int', 'bool', 'float')


def upgrade(active_plugins=None, options=None):
    op.create_table(
        'user_preferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('key', sa.Unicode(100), nullable=False),
        sa.Column('type', pref_type_enum, nullable=False),
        sa.Column('value', sa.Unicode(255), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade(active_plugins=None, options=None):
    op.drop_table('user_preferences')
