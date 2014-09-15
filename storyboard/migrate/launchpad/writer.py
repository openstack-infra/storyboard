# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import json
import sys

from openid.consumer import consumer
from openid import cryptutil

import storyboard.common.event_types as event_types
from storyboard.db.api import base as db_api
from storyboard.db.api import comments as comments_api
from storyboard.db.api import projects as projects_api
from storyboard.db.api import tags as tags_api
from storyboard.db.api import users as users_api
from storyboard.db.models import Story
from storyboard.db.models import Task
from storyboard.db.models import TimeLineEvent


class LaunchpadWriter(object):
    def __init__(self, project_name):
        """Create a new instance of the launchpad-to-storyboard data writer.
        """

        # username -> openid
        self._openid_map = dict()
        # openid -> SB User Entity
        self._user_map = dict()
        # tag_name -> SB StoryTag Entity
        self._tag_map = dict()

        # SB Project Entity + Sanity check.
        self.project = projects_api.project_get_by_name(project_name)
        if not self.project:
            print "Local project %s not found in storyboard, please create " \
                  "it first." % (project_name)
            sys.exit(1)

    def write_tags(self, bug):
        """Extracts the tags from a launchpad bug, seeds/loads them in the
        StoryBoard database, and returns a list of the corresponding entities.
        """
        tags = list()

        # Make sure the tags field exists and has some content.
        if hasattr(bug, 'tags') and bug.tags:
            for tag_name in bug.tags:
                tags.append(self.build_tag(tag_name))

        return tags

    def build_tag(self, tag_name):
        """Retrieve the SQLAlchemy record for the given tag name, creating it
        if necessary.

        :param tag_name: Name of the tag to retrieve and/or create.
        :return: The SQLAlchemy entity corresponding to the tag name.
        """
        if tag_name not in self._tag_map:

            # Does it exist in the database?
            tag = tags_api.tag_get_by_name(tag_name)

            if not tag:
                # Go ahead and create it.
                print "Importing tag '%s'" % (tag_name)
                tag = tags_api.tag_create(dict(
                    name=tag_name
                ))

            # Add it to our memory cache
            self._tag_map[tag_name] = tag

        return self._tag_map[tag_name]

    def write_user(self, lp_user):
        """Writes a launchpad user record into our user cache, resolving the
        openid if necessary.

        :param lp_user: The launchpad user record.
        :return: The SQLAlchemy entity for the user record.
        """
        if lp_user is None:
            return lp_user

        username = lp_user.name
        display_name = lp_user.display_name

        # Resolve the openid.
        if username not in self._openid_map:
            openid_consumer = consumer.Consumer(
                dict(id=cryptutil.randomString(16, '0123456789abcdef')), None)
            openid_request = openid_consumer.begin(lp_user.web_link)
            openid = openid_request.endpoint.getLocalID()

            self._openid_map[username] = openid

        openid = self._openid_map[username]

        # Resolve the user record from the openid.
        if openid not in self._user_map:

            # Check for the user, create if new.
            user = users_api.user_get_by_openid(openid)
            if not user:
                print "Importing user '%s'" % (username)

                # Use a temporary email address, since LP won't give this to
                # us and it'll be updated on first login anyway.
                user = users_api.user_create({
                    'username': username,
                    'openid': openid,
                    'full_name': display_name,
                    'email': "%s@example.com" % (username)
                })

            self._user_map[openid] = user

        return self._user_map[openid]

    def write_bug(self, owner, assignee, priority, status, tags, bug):
        """Writes the story, task, task history, and conversation.

        :param owner: The bug owner SQLAlchemy entity.
        :param tags: The tag SQLAlchemy entities.
        :param bug: The Launchpad Bug record.
        """

        if hasattr(bug, 'date_created'):
            created_at = bug.date_created.strftime('%Y-%m-%d %H:%M:%S')
        else:
            created_at = None

        if hasattr(bug, 'date_last_updated'):
            updated_at = bug.date_last_updated.strftime('%Y-%m-%d %H:%M:%S')
        else:
            updated_at = None

        print "Importing %s" % (bug.self_link)
        story = db_api.entity_create(Story, {
            'description': bug.description,
            'created_at': created_at,
            'creator': owner,
            'is_bug': True,
            'title': bug.title,
            'updated_at': updated_at,
            'tags': tags
        })

        task = db_api.entity_create(Task, {
            'title': bug.title,
            'assignee_id': assignee.id if assignee else None,
            'project_id': self.project.id,
            'story_id': story.id,
            'created_at': created_at,
            'updated_at': updated_at,
            'priority': priority,
            'status': status
        })

        # Create the creation event for the story manually, so we don't trigger
        # event notifications.
        db_api.entity_create(TimeLineEvent, {
            'story_id': story.id,
            'author_id': owner.id,
            'event_type': event_types.STORY_CREATED,
            'created_at': created_at
        })

        # Create the creation event for the task.
        db_api.entity_create(TimeLineEvent, {
            'story_id': story.id,
            'author_id': owner.id,
            'event_type': event_types.TASK_CREATED,
            'created_at': created_at,
            'event_info': json.dumps({
                'task_id': task.id,
                'task_title': task.title
            })
        })

        # Create the discussion.
        comment_count = 0
        for message in bug.messages:
            message_created_at = message.date_created \
                .strftime('%Y-%m-%d %H:%M:%S')
            message_owner = self.write_user(message.owner)

            comment = comments_api.comment_create({
                'content': message.content,
                'created_at': message_created_at
            })

            db_api.entity_create(TimeLineEvent, {
                'story_id': story.id,
                'author_id': message_owner.id,
                'event_type': event_types.USER_COMMENT,
                'comment_id': comment.id,
                'created_at': message_created_at
            })

            comment_count += 1
            print '- Imported %d comments\r' % (comment_count),

        # Advance the stdout line
        print ''

        return story
