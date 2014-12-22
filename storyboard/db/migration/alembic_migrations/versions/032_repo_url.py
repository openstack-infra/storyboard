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

"""This migration adds new column for git repo to projects table

Revision ID: 031
Revises: 030
Create Date: 2014-12-30 14:55:09.622503

"""

# revision identifiers, used by Alembic.

revision = '032'
down_revision = '031'

from alembic import op
from sqlalchemy import Column
from sqlalchemy import String


def upgrade(active_plugins=None, options=None):
    op.add_column('projects', Column('repo_url',
                                     String(255),
                                     default=None,
                                     nullable=True))


def downgrade(active_plugins=None, options=None):
    op.drop_column('projects', 'repo_url')
