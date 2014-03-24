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

"""Remove legacy priority column

Revision ID: 009
Revises: 008
Create Date: 2014-03-24 14:00:19.159763

"""

# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'


from alembic import op
import sqlalchemy as sa

MYSQL_ENGINE = 'InnoDB'
MYSQL_CHARSET = 'utf8'


def _define_enums():
    storyboard_priority = sa.Enum(
        'Undefined', 'Low', 'Medium', 'High', 'Critical',
        name='priority')

    return {
        'storyboard_priority': storyboard_priority
    }


def upgrade(active_plugins=None, options=None):
    op.drop_column('stories', 'priority')

    # Need to explicitly delete enums during migrations for Postgres
    enums = _define_enums()
    for enum in enums.values():
        enum.drop(op.get_bind())


def downgrade(active_plugins=None, options=None):
    enums = _define_enums()
    for enum in enums.values():
        enum.create(op.get_bind())

    op.add_column('stories', sa.Column('priority',
                                       enums['storyboard_priority'],
                                       nullable=True))
