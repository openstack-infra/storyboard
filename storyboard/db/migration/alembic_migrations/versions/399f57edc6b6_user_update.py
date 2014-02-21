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

"""user update

Revision ID: 399f57edc6b6
Revises: 18708bcdc0fe
Create Date: 2014-02-21 13:21:59.917098

"""

# revision identifiers, used by Alembic.
revision = '399f57edc6b6'
down_revision = '18708bcdc0fe'


from alembic import op
import sqlalchemy as sa

MYSQL_ENGINE = 'InnoDB'
MYSQL_CHARSET = 'utf8'


def upgrade(active_plugins=None, options=None):

    op.drop_column('users', 'password')
    op.add_column('users', sa.Column('openid', sa.String(255)))


def downgrade(active_plugins=None, options=None):

    op.add_column('users', sa.Column('password', sa.UnicodeText))
    op.drop_column('users', 'openid')
