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

"""This migration adds the 'story_title' to the 'events_info' column of
'subscription_events' table for tags_added and tags_deleted events.

Revision ID: 051
Revises: 050
Create Date: 2015-12-03 12:00:00

"""

# revision identifiers, used by Alembic.

revision = '051'
down_revision = '050'

from alembic import op
import json
import sqlalchemy as sa
from sqlalchemy.sql import column
from sqlalchemy.sql.expression import table


subs_events_table = table(
    'subscription_events',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('event_type', sa.String(convert_unicode=True)),
    sa.Column('event_info', sa.String(convert_unicode=True))
)


def upgrade(active_plugins=None, options=None):

    bind = op.get_bind()

    stories_dict = {}
    for story in bind.execute(
            sa.select(columns=[column('id'), column('title')],
                      from_obj=sa.Table('stories',
                                        sa.MetaData()))):
        stories_dict[story.id] = story.title

    events = bind.execute(
        subs_events_table.select().where(
            sa.sql.or_(
                subs_events_table.c.event_type == "tags_added",
                subs_events_table.c.event_type == "tags_deleted"
            )
        )
    )

    # Add story_title in event_info object for every tag event
    for event in events:

        event_info_obj = json.loads(event.event_info)

        # Update event_info to add story_title
        if 'story_title' not in event_info_obj:
            event_info_obj['story_title'] = stories_dict[
                event_info_obj['story_id']
            ]

        new_event_info = json.dumps(event_info_obj)

        # Update event with updated event_info
        bind.execute(
            subs_events_table.update().where(
                subs_events_table.c.id == event.id
            ).values(event_info=new_event_info)
        )


def downgrade(active_plugins=None, options=None):

    bind = op.get_bind()

    events = bind.execute(
        subs_events_table.select().where(
            sa.sql.or_(
                subs_events_table.c.event_type == "tags_added",
                subs_events_table.c.event_type == "tags_deleted"
            )
        )
    )
    # Remove story_title from event_info of tag events
    for event in events:

        event_info_obj = json.loads(event.event_info)

        # Delete story_title if exists
        if 'story_title' in event_info_obj:
            del event_info_obj['story_title']

        new_event_info = json.dumps(event_info_obj)

        # Update event with updated event_info
        bind.execute(
            subs_events_table.update().where(
                subs_events_table.c.id == event.id
            ).values(event_info=new_event_info)
        )
