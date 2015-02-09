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

"""This migration creates a reference between oauth access tokens and refresh
tokens.

Revision ID: 034
Revises: 033
Create Date: 2015-02-06 12:00:00

"""

# revision identifiers, used by Alembic.

revision = '034'
down_revision = '033'

from alembic import op
from sqlalchemy import Column
from sqlalchemy import Integer


def upgrade(active_plugins=None, options=None):
    op.add_column('refreshtokens', Column('access_token_id',
                                          Integer(),
                                          nullable=False))


def downgrade(active_plugins=None, options=None):
    op.drop_column('refreshtokens', 'access_token_id')
