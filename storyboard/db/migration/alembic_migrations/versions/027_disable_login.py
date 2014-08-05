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

"""Adds enable_login flag to users table.

Revision ID: 027
Revises: 026
Create Date: 2014-08-06 01:00:00

"""

# revision identifiers, used by Alembic.
revision = '027'
down_revision = '026'


from alembic import op
from sqlalchemy import Boolean
from sqlalchemy import Column


def upgrade(active_plugins=None, options=None):
    op.add_column('users',
                  Column('enable_login',
                         Boolean(),
                         default=True,
                         server_default="1",
                         nullable=False))


def downgrade(active_plugins=None, options=None):
    op.drop_column('users', 'enable_login')
