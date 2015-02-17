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

"""This migration creates a new index on accesstokens table
for the access_token column.

Revision ID: 040
Revises: 039
Create Date: 2015-02-17 12:00:00

"""

# revision identifiers, used by Alembic.

revision = '040'
down_revision = '039'

from alembic import op


def upgrade(active_plugins=None, options=None):
    op.create_index('accesstokens_access_token_idx',
        'accesstokens', ['access_token'])


def downgrade(active_plugins=None, options=None):
    op.drop_index('accesstokens_access_token_idx')
