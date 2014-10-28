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
from storyboard.db.api import project_groups as project_groups_api
from storyboard.db.api import subscription_events as sub_events_api
from storyboard.db.api import subscriptions as subscriptions_api
from storyboard.db.api import tasks as tasks_api


def handle_timeline_events(event, author_id):

    target_subs = []
    user_ids = set()

    story_id = event.story_id
    if event.event_info:
        event_info = json.loads(event.event_info)
        task_id = event_info.get("task_id")

        # Handling tasks targeted.
        target_sub = subscriptions_api.subscription_get_all_by_target(
            ['task'], task_id)
        target_subs.extend(target_sub)

    # Handling stories targeted.
    target_sub = subscriptions_api.subscription_get_all_by_target(
        ['story'], story_id)
    target_subs.extend(target_sub)

    # Handling projects, project groups targeted for stories without tasks.

    tasks = tasks_api.task_get_all(story_id=story_id)

    for task in tasks:
        project_id = task.project_id

        # Handling projects targeted.
        target_sub = subscriptions_api.subscription_get_all_by_target(
            ['project'], project_id)
        target_subs.extend(target_sub)

        # Handling project groups targeted.
        pgs = project_groups_api.project_group_get_all(project_id=project_id)
        for pg in pgs:
            target_sub = subscriptions_api.subscription_get_all_by_target(
                ['project_group'], pg.id)
            target_subs.extend(target_sub)

    for sub in target_subs:
        user_ids.add(sub.user_id)

    for user_id in user_ids:
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


def handle_resources(method, resource_id, sub_resource_id, author_id):

    target_subs = []
    user_ids = set()

    if sub_resource_id:

        # Handling project addition/deletion to/from project_group.
        target_sub = subscriptions_api.subscription_get_all_by_target(
            ['project'], sub_resource_id)
        target_subs.extend(target_sub)

        for sub in target_subs:
            user_ids.add(sub.user_id)

        for user_id in user_ids:

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
            target_sub = subscriptions_api.subscription_get_all_by_target(
                ['project_group'], resource_id)
            target_subs.extend(target_sub)

            for sub in target_subs:
                user_ids.add(sub.user_id)

            for user_id in user_ids:
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
    comment_id = event.comment_id
    comment = comments_api.comment_get(comment_id)
    comment_content = comment.content
    return json.dumps({'comment_id': comment_id, 'comment_content':
                      comment_content})
