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

"""The refresh token should also have expiration fields.

Revision ID: 019
Revises: 018
Create Date: 2014-05-21 11:17:16.360987

"""

# revision identifiers, used by Alembic.
revision = '019'
down_revision = '018'


from alembic import op
import sqlalchemy as sa


def upgrade(active_plugins=None, options=None):

    # Deleting old tokens because they don't have a valid expiration
    # information.
    bind = op.get_bind()
    bind.execute(sa.delete(table='refreshtokens'))

    op.add_column('refreshtokens', sa.Column('expires_at', sa.DateTime(),
                                             nullable=False))
    op.add_column('refreshtokens', sa.Column('expires_in', sa.Integer(),
                                             nullable=False))
    ### end Alembic commands ###


def downgrade(active_plugins=None, options=None):

    op.drop_column('refreshtokens', 'expires_in')
    op.drop_column('refreshtokens', 'expires_at')
    ### end Alembic commands ###
