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

"""This migration adds a column where we can store the ID of the person
who triggered the event.

Revision ID: 025
Revises: 024
Create Date: 2014-09-08 13:21:59.917098

"""

# revision identifiers, used by Alembic.
revision = '025'
down_revision = '024'

from alembic import op
import sqlalchemy as sa


def upgrade(active_plugins=None, options=None):
    op.add_column('subscription_events', sa.Column('author_id', sa.Integer()))


def downgrade(active_plugins=None, options=None):
    op.drop_column('subscription_events', 'author_id')
