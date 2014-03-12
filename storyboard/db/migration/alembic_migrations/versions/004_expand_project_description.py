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

"""Expand project description

Revision ID: 004
Revises: 003
Create Date: 2014-03-05 17:03:12.978207

"""

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'

from alembic import op
import sqlalchemy as sa

MYSQL_ENGINE = 'InnoDB'
MYSQL_CHARSET = 'utf8'


def change_type(type):
    column_old = 'description'
    column_new = column_old + '_new'
    bind = op.get_bind()
    meta = sa.MetaData(bind.engine)
    projects = sa.Table('projects', meta, autoload=True)
    new_column = sa.Column(column_new, type)
    new_column.create(projects)
    projects.update().values(description_new=projects.c[column_old]).execute()
    projects.c[column_old].drop()
    projects.c[column_new].alter(name=column_old)


def upgrade(active_plugins=None, options=None):

    change_type(sa.UnicodeText)


def downgrade(active_plugins=None, options=None):

    change_type(sa.Unicode(100))
