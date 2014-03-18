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

"""empty message

Revision ID: 007
Revises: 006
Create Date: 2014-04-18 14:55:09.622503

"""

# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'

from alembic import op
from sqlalchemy import Boolean
from sqlalchemy import Column


def upgrade(active_plugins=None, options=None):
    op.add_column('comments',
                  Column('is_active',
                         Boolean(),
                         default=True,
                         server_default="1",
                         nullable=False))


def downgrade(active_plugins=None, options=None):
    op.drop_column('comments', 'is_active')
