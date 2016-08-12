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
# implied. See the License for the specific language governing permissions and
# limitations under the License.

import json

import storyboard.db.api.base as db_api
from storyboard.db.api import subscriptions as sub_api
from storyboard.db.api import timeline_events as events_api
import storyboard.db.models as models
from storyboard.plugin.event_worker import WorkerTaskBase


def get_preference(name, user):
    if name not in user.preferences:
        return None
    return user.preferences[name].cast_value


class Subscription(WorkerTaskBase):
    def enabled(self):
        """This plugin is always enabled.

        :return: True
        """
        return True

    def handle(self, session, author, method, url, path, query_string, status,
               resource, resource_id, sub_resource=None, sub_resource_id=None,
               resource_before=None, resource_after=None):
        """This worker handles API events and attempts to determine whether
        they correspond to user subscriptions.

        :param session: An event-specific SQLAlchemy session.
        :param author: The author's user record.
        :param method: The HTTP Method.
        :param url: The Referer header from the request.
        :param path: The full HTTP Path requested.
        :param query_string: The HTTP query string from the request.
        :param status: The returned HTTP Status of the response.
        :param resource: The resource type.
        :param resource_id: The ID of the resource.
        :param sub_resource: The subresource type.
        :param sub_resource_id: The ID of the subresource.
        :param resource_before: The resource state before this event occurred.
        :param resource_after: The resource state after this event occurred.
        """
        if resource == 'timeline_event':
            story_id = resource_after.get('story_id')
            worklist_id = resource_after.get('worklist_id')
            if story_id is not None:
                subscribers = sub_api.subscription_get_all_subscriber_ids(
                    'story', story_id, session=session)
                self.handle_timeline_events(
                    session, resource_after, author, subscribers)
            if worklist_id is not None:
                subscribers = sub_api.subscription_get_all_subscriber_ids(
                    'worklist', worklist_id, session=session)
                self.handle_timeline_events(
                    session, resource_after, author, subscribers)

        elif resource == 'project_group':
            subscribers = sub_api.subscription_get_all_subscriber_ids(
                resource, resource_id, session=session)
            self.handle_resources(session=session,
                                  method=method,
                                  resource_id=resource_id,
                                  sub_resource_id=sub_resource_id,
                                  author=author,
                                  subscribers=subscribers)

        if method == 'DELETE' and not (sub_resource_id or sub_resource):
            self.handle_deletions(session, resource, resource_id)

    def handle_deletions(self, session, resource_name, resource_id):
        target_subs = []
        sub_ids = set()
        resource_name = resource_name[:-1]

        target_sub = db_api.entity_get_all(models.Subscription,
                                           target_type=resource_name,
                                           target_id=resource_id,
                                           session=session)
        target_subs.extend(target_sub)

        for sub in target_subs:
            sub_ids.add(sub.id)

        for sub_id in sub_ids:
            db_api.entity_hard_delete(models.Subscription,
                                      sub_id,
                                      session=session)

    def handle_timeline_events(self, session, resource, author, subscribers):

        for user_id in subscribers:
            user = db_api.entity_get(models.User, user_id, session=session)
            send_notification = get_preference(
                'receive_notifications_worklists', user)
            if (send_notification != 'true' and
                    resource.get('worklist_id') is not None):
                continue

            if resource['event_type'] == 'user_comment':
                event_info = json.dumps(
                    self.resolve_comments(session=session, event=resource)
                )

            else:
                event_info = resource['event_info']

            # Don't send a notification if the user isn't allowed to see the
            # thing this event is about.
            event = events_api.event_get(
                resource['id'], current_user=user_id, session=session)
            if not events_api.is_visible(event, user_id, session=session):
                continue

            db_api.entity_create(models.SubscriptionEvents, {
                "author_id": author.id,
                "subscriber_id": user_id,
                "event_type": resource['event_type'],
                "event_info": event_info
            }, session=session)

    def handle_resources(self, session, method, resource_id, sub_resource_id,
                         author, subscribers):

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

                db_api.entity_create(models.SubscriptionEvents, {
                    "author_id": author.id,
                    "subscriber_id": user_id,
                    "event_type": event_type,
                    "event_info": event_info
                }, session=session)

        else:
            if method == 'DELETE':
                # Handling project_group targeted.
                for user_id in subscribers:
                    db_api.entity_create(models.SubscriptionEvents, {
                        "author_id": author.id,
                        "subscriber_id": user_id,
                        "event_type": 'project_group deleted',
                        "event_info": json.dumps(
                            {'project_group_id': resource_id})
                    }, session=session)

    def resolve_comments(self, session, event):

        # Sanity check. If there's no comment_id, exit.
        if 'comment_id' not in event:
            return None

        # Retrieve the content of the comment.
        comment = db_api.entity_get(models.Comment,
                                    event['comment_id'],
                                    session=session)
        if not comment:
            return None

        # Retrieve the timeline events.
        timeline_event = session.query(models.TimeLineEvent) \
            .filter(models.TimeLineEvent.comment_id == event['comment_id']) \
            .first()
        if not timeline_event:
            return None

        # Retrieve the story from the timeline event.
        story = db_api.entity_get(models.Story,
                                  timeline_event.story_id,
                                  session=session)
        if not story:
            return None

        # Construct and return the comment's event_info object.
        return {
            'comment_id': comment.id,
            'comment_content': comment.content,
            'story_id': story.id,
            'story_title': story.title
        }
