# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json

from storyboard.db.api import comments as comments_api
from storyboard.db.api import stories as story_api
from storyboard.db.api import subscription_events as sub_events_api
from storyboard.db.api import subscriptions as subscriptions_api
from storyboard.db.api import timeline_events as timeline_api


def handle_timeline_events(event, author_id, subscribers):

    for user_id in subscribers:
        if event.event_type == 'user_comment':
            event_info = resolve_comments(event)

        else:
            event_info = event.event_info

        sub_events_api.subscription_events_create({
            "author_id": author_id,
            "subscriber_id": user_id,
            "event_type": event.event_type,
            "event_info": event_info
        })


def handle_resources(method, resource_id, sub_resource_id, author_id,
                     subscribers):

    if sub_resource_id:

        for user_id in subscribers:

            if method == 'DELETE':
                event_type = 'project removed from project_group'
                event_info = json.dumps({'project_group_id': resource_id,
                                         'project_id': sub_resource_id})

            else:
                event_type = 'project added to project_group'
                event_info = json.dumps({'project_group_id': resource_id,
                                         'project_id': sub_resource_id})

            sub_events_api.subscription_events_create({
                "author_id": author_id,
                "subscriber_id": user_id,
                "event_type": event_type,
                "event_info": event_info
            })

    else:
        if method == 'DELETE':
            # Handling project_group targeted.
            for user_id in subscribers:
                sub_events_api.subscription_events_create({
                    "author_id": author_id,
                    "subscriber_id": user_id,
                    "event_type": 'project_group deleted',
                    "event_info": json.dumps({'project_group_id': resource_id})
                })


def handle_deletions(resource_name, resource_id):
    target_subs = []
    sub_ids = set()
    resource_name = resource_name[:-1]

    target_sub = subscriptions_api.subscription_get_all_by_target(
        resource_name, resource_id)
    target_subs.extend(target_sub)

    for sub in target_subs:
        sub_ids.add(sub.id)

    for sub_id in sub_ids:
        subscriptions_api.subscription_delete(sub_id)


def resolve_comments(event):
    event_info = {
        'comment_id': event.comment_id or None,
    }

    # Retrieve the content of the comment.
    comment = comments_api.comment_get(event.comment_id)
    event_info['comment_content'] = comment.content

    # Retrieve the story ID of the comment.
    timeline_events = timeline_api.events_get_all(comment_id=event.comment_id)
    if timeline_events:
        story = story_api.story_get(timeline_events[0].story_id)

        if story:
            event_info['story_id'] = story.id
            event_info['story_title'] = story.title

    return json.dumps(event_info)
