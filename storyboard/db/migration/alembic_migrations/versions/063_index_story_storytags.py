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

"""index story_storytags

Revision ID: a6e048164572
Revises: 062
Create Date: 2018-06-25 17:13:43.992561

"""

# revision identifiers, used by Alembic.
revision = '063'
down_revision = '062'


from alembic import op


def upgrade(active_plugins=None, options=None):
    op.create_index('story_storytags_idx',
                    'story_storytags', ['story_id'])


def downgrade(active_plugins=None, options=None):
    op.drop_index('story_storytags_idx')
