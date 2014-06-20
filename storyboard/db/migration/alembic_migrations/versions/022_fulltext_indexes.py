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

"""Adding full text indexes

Revision ID: 022
Revises: 021
Create Date: 2014-07-11 14:08:08.129484

"""

# revision identifiers, used by Alembic.
revision = '022'
down_revision = '021'


from alembic import op

from storyboard.openstack.common import log

LOG = log.getLogger(__name__)


def upgrade(active_plugins=None, options=None):

    version_info = op.get_bind().engine.dialect.server_version_info
    if version_info[0] < 5 or version_info[0] == 5 and version_info[1] < 6:
        LOG.warn("MySQL version is lower than 5.6. Skipping full-text indexes")
        return

    # Index for projects
    op.execute("ALTER TABLE projects "
               "ADD FULLTEXT projects_fti (name, description)")

    # Index for stories
    op.execute("ALTER TABLE stories "
               "ADD FULLTEXT stories_fti (title, description)")

    # Index for tasks
    op.execute("ALTER TABLE tasks ADD FULLTEXT tasks_fti (title)")

    # Index for comments
    op.execute("ALTER TABLE comments ADD FULLTEXT comments_fti (content)")

    # Index for users
    op.execute("ALTER TABLE users "
               "ADD FULLTEXT users_fti (username, full_name, email)")


def downgrade(active_plugins=None, options=None):

    version_info = op.get_bind().engine.dialect.server_version_info
    if version_info[0] < 5 or version_info[0] == 5 and version_info[1] < 6:
        LOG.warn("MySQL version is lower than 5.6. Skipping full-text indexes")
        return

    op.drop_index("projects_fti", table_name='projects')
    op.drop_index("stories_fti", table_name='stories')
    op.drop_index("tasks_fti", table_name='tasks')
    op.drop_index("comments_fti", table_name='comments')
    op.drop_index("users_fti", table_name='users')
