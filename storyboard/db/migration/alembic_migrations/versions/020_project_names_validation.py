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

"""Existing projects should be renamed if they do not pass a new validation.
The previous name will be appended to the description so that it can be
restored.

Revision ID: 020
Revises: 019
Create Date: 2014-06-23 12:50:43.924601

"""

# revision identifiers, used by Alembic.
revision = '020'
down_revision = '019'


from alembic import op
import sqlalchemy as sa
from sqlalchemy import MetaData
from sqlalchemy.sql.expression import table

from storyboard.common.custom_types import NameType


def upgrade(active_plugins=None, options=None):

    bind = op.get_bind()
    validator = NameType()

    projects = list(bind.execute(
        sa.select(columns=['*'], from_obj=sa.Table('projects', MetaData()))))

    projects_table = table(
        'projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.UnicodeText(), nullable=True),
    )

    last_idx = 0

    for project in projects:
        project_name = project["name"]
        project_id = project["id"]
        need_rename = False

        try:
            validator.validate(project_name)
        except Exception:
            need_rename = True

        if need_rename:
            # This project needs renaming
            temp_name = "Project-%d" % last_idx
            last_idx += 1
            updated_description = "%s This project was renamed to fit new " \
                                  "naming validation. Original name was: %s" \
                                  % (project["description"], project_name)

            bind.execute(projects_table.update()
                         .where(projects_table.c.id == project_id)
                         .values(name=temp_name,
                                 description=updated_description))


def downgrade(active_plugins=None, options=None):
    # No way back for invalid names
    pass
