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

"""Allow subscription to worklists

Revision ID: 058
Revises: 057
Create Date: 2016-06-01 13:28:19.033906

"""

# revision identifiers, used by Alembic.
revision = '058'
down_revision = '057'


from alembic import op
import sqlalchemy as sa

old_type_enum = sa.Enum('task', 'story', 'project', 'project_group')
new_type_enum = sa.Enum(
    'task', 'story', 'project', 'project_group', 'worklist')


def upgrade(active_plugins=None, options=None):
    dialect = op.get_bind().engine.dialect
    if dialect.supports_alter:
        op.alter_column('subscriptions',
                        'target_type',
                        existing_type=old_type_enum,
                        type_=new_type_enum)


def downgrade(active_plugins=None, options=None):
    op.alter_column('subscriptions',
                    'target_type',
                    existing_type=new_type_enum,
                    type_=old_type_enum)
