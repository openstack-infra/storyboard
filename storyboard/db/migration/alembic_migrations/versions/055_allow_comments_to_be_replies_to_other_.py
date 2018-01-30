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

"""Allow comments to be replies to other comments

Revision ID: 055
Revises: 054
Create Date: 2016-03-05 23:35:40.379333

"""

# revision identifiers, used by Alembic.
revision = '055'
down_revision = '054'


from alembic import op
import sqlalchemy as sa


def upgrade(active_plugins=None, options=None):
    op.add_column(
        'comments', sa.Column('in_reply_to', sa.Integer(), nullable=True))
    dialect = op.get_bind().engine.dialect
    if dialect.supports_alter:
        op.create_foreign_key(
            'comments_ibfk_1', 'comments', 'comments', ['in_reply_to'], ['id'])


def downgrade(active_plugins=None, options=None):
    op.drop_constraint('comments_ibfk_1', 'comments', type_='foreignkey')
    op.drop_column('comments', 'in_reply_to')
