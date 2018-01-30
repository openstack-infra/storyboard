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

"""extends project name and project group name length to 100

Revision ID: 061
Revises: 060
Create Date: 2017-03-17 10:28:24.567704

"""

# revision identifiers, used by Alembic.
revision = '061'
down_revision = '060'


from alembic import op
import sqlalchemy as sa


def upgrade(active_plugins=None, options=None):
    dialect = op.get_bind().engine.dialect
    if dialect.supports_alter:
        op.alter_column('project_groups', 'name', type_=sa.Unicode(100))
        op.alter_column('projects', 'name', type_=sa.Unicode(100))


def downgrade(active_plugins=None, options=None):

    op.alter_column('project_groups', 'name', type_=sa.Unicode(50))
    op.alter_column('projects', 'name', type_=sa.Unicode(50))
