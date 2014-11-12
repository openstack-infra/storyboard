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

"""Modifies the type of the comment content column to be mysql's MEDIUMTEXT
rather than TEXT. This increases the size limit from 2^16 bytes to 2^24 bytes.

Revision ID: 030
Revises: 029
Create Date: 2014-11-12 01:00:00

"""

# revision identifiers, used by Alembic.
revision = '030'
down_revision = '029'

from alembic import op
import sqlalchemy as sa

from storyboard.db.models import MYSQL_MEDIUM_TEXT


def upgrade(active_plugins=None, options=None):
    op.alter_column('comments', 'content', type_=MYSQL_MEDIUM_TEXT)


def downgrade(active_plugins=None, options=None):
    op.alter_column('comments', 'content', type_=sa.UnicodeText)
