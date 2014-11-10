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

"""Remove the user name uniqueness restriction.

Revision ID: 029
Revises: 028
Create Date: 2014-11-10 01:00:00

"""

# revision identifiers, used by Alembic.
revision = '029'
down_revision = '028'

from alembic import op


def upgrade(active_plugins=None, options=None):
    op.drop_constraint('uniq_user_username', 'users', type_='unique')


def downgrade(active_plugins=None, options=None):
    op.create_unique_constraint("uniq_user_username", "users", ["username"])
