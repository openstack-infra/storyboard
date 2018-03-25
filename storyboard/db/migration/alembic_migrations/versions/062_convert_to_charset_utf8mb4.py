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

"""convert to charset utf8mb4

Revision ID: 062
Revises: 061
Create Date: 2018-03-23 14:34:55.656531

"""

# revision identifiers, used by Alembic.
revision = '062'
down_revision = '061'


from alembic import op
from sqlalchemy import inspect


def upgrade(active_plugins=None, options=None):
    dialect = op.get_bind().engine.dialect
    if dialect.name == 'mysql' and dialect.supports_alter:
        for table in inspect(op.get_bind()).get_table_names():
            op.execute('ALTER TABLE %s CONVERT TO CHARACTER SET utf8mb4' %
                       table)


def downgrade(active_plugins=None, options=None):
    dialect = op.get_bind().engine.dialect
    if dialect.name == 'mysql' and dialect.supports_alter:
        for table in inspect(op.get_bind()).get_table_names():
            op.execute('ALTER TABLE %s CONVERT TO CHARACTER SET utf8' %
                       table)
