# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
#
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

"""This migration changes length of a valid storytag from 20 to 50

Revision ID: 026
Revises: 025
Create Date: 2014-09-23 00:00:00

"""

# revision identifiers, used by Alembic.
revision = '026'
down_revision = '025'

from alembic import op
import sqlalchemy as sa


def upgrade(active_plugins=None, options=None):
    op.alter_column(
        'storytags', 'name',
        type_=sa.String(length=50))


def downgrade(active_plugins=None, options=None):
    op.alter_column(
        'storytags', 'name',
        type_=sa.String(length=20))
