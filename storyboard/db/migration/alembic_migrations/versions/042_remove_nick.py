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

"""This migration removes the 'nickname' column from the user table.

Revision ID: 042
Revises: 041
Create Date: 2015-02-17 12:00:00

"""

# revision identifiers, used by Alembic.

revision = '042'
down_revision = '041'

from alembic import op
from oslo_log import log
import sqlalchemy as sa

LOG = log.getLogger(__name__)


def upgrade(active_plugins=None, options=None):
    op.drop_column('users', 'username')

    # Handle the FT Index on the user table.
    version_info = op.get_bind().engine.dialect.server_version_info
    if version_info[0] < 5 or version_info[0] == 5 and version_info[1] < 6:
        LOG.warning(
            "MySQL version is lower than 5.6. Skipping full-text indexes")
        return

    # Index for users
    op.drop_index("users_fti", table_name='users')
    op.execute("ALTER TABLE users "
               "ADD FULLTEXT users_fti (full_name, email)")


def downgrade(active_plugins=None, options=None):
    op.add_column(
        'users',
        sa.Column('username', sa.Unicode(length=30), nullable=True),
    )

    version_info = op.get_bind().engine.dialect.server_version_info
    if version_info[0] < 5 or version_info[0] == 5 and version_info[1] < 6:
        LOG.warning(
            "MySQL version is lower than 5.6. Skipping full-text indexes")
        return

    # Index for users
    op.drop_index("users_fti", table_name='users')
    op.execute("ALTER TABLE users "
               "ADD FULLTEXT users_fti (username, full_name, email)")
