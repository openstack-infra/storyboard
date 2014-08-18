# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import json
import sys
import warnings

from launchpadlib import launchpad
from openid.consumer import consumer
from openid import cryptutil
from sqlalchemy.exc import SADeprecationWarning

from storyboard.common import event_types
from storyboard.db.api import base as db_api
from storyboard.db.models import Comment
from storyboard.db.models import Story
from storyboard.db.models import StoryTag
from storyboard.db.models import Task
from storyboard.db.models import TimeLineEvent
from storyboard.db.models import User

warnings.simplefilter("ignore", SADeprecationWarning)
user_openid_map = dict()
user_obj_map = dict()
tag_obj_map = dict()


def map_openid(username):

    if username is None:
        return username

    if username not in user_openid_map:

        openid_consumer = consumer.Consumer(
            dict(id=cryptutil.randomString(16, '0123456789abcdef')), None)
        openid_request = openid_consumer.begin(
            "https://launchpad.net/~%s" % username)

        user_openid_map[username] = openid_request.endpoint.getLocalID()

    return dict(name=username, openid=user_openid_map[username])


def map_priority(importance):
    if importance in ('Unknown', 'Undecided', 'Medium'):
        return 'medium'
    elif importance in ('Critical', 'High'):
        return 'high'
    return 'low'


def map_status(status):
    ('todo', 'inprogress', 'invalid', 'review', 'merged')
    if status in ('Unknown', 'New', 'Confirmed', 'Triaged'):
        return 'todo'
    elif status in (
            'Incomplete', 'Opinion', 'Invalid', "Won't Fix", 'Expired'):
        return 'invalid'
    elif status == 'In Progress':
        return 'inprogress'
    elif status in ('Fix Committed', 'Fix Released'):
        return 'merged'


def fetch_bugs(project_name='openstack-ci'):
    lp = launchpad.Launchpad.login_anonymously('storyboard', 'production')

    project_name = project_name
    project = lp.projects[project_name]

    tasks = []

    for task in project.searchTasks():
        messages = []
        bug = task.bug
        for message in bug.messages:
            messages.append(dict(
                author=map_openid(message.owner.name),
                content=message.content,
                created_at=message.date_created.strftime(
                    '%Y-%m-%d %H:%M:%S %z'),
            ))

        tasks.append(dict(
            bug=dict(
                creator=map_openid(bug.owner.name),
                title=bug.title,
                description=bug.description,
                created_at=bug.date_created.strftime('%Y-%m-%d %H:%M:%S %z'),
                updated_at=bug.date_last_updated.strftime(
                    '%Y-%m-%d %H:%M:%S %z'),
                is_bug=True,
                tags=bug.tags,
            ),
            task=dict(
                creator=map_openid(task.owner.name),
                status=map_status(task.status),
                assignee=map_openid((task.assignee and task.assignee.name)),
                priority=map_priority(task.importance),
                created_at=task.date_created.strftime('%Y-%m-%d %H:%M:%S %z'),
            ),
            messages=messages,
        ))

    return tasks


def get_user(user, session):
    if user is None:
        return user

    if user['name'] not in user_obj_map:
        db_user = session.query(User).filter_by(username=user["name"]).first()
        if not db_user:
            db_user = User()
            user.username = user['name']
            user.openid = user['openid']
            user.email = "%s@example.com" % user['name']
            user.last_login = datetime.datetime.now()
            session.add(db_user)
        user_obj_map[user['name']] = db_user
    return user_obj_map[user['name']]


def get_tag(tag, session):
    if tag not in tag_obj_map:
        db_tag = session.query(StoryTag).filter_by(name=tag).first()
        if not db_tag:
            db_tag = StoryTag()
            db_tag.name = tag
            session.add(db_tag)
        tag_obj_map[tag] = db_tag
    return tag_obj_map[tag]


def write_tasks(tasks):

    session = db_api.get_session()

    with session.begin():

        for collection in tasks:
            bug = collection['bug']
            task = collection['task']
            messages = collection['messages']

            # First create the bug, then tags, then task, then comments
            story_obj = Story()
            story_obj.description = bug['description']
            story_obj.created_at = bug['created_at']
            story_obj.creator = get_user(bug['creator'], session)
            story_obj.is_bug = True
            story_obj.title = bug['title']
            story_obj.updated_at = bug['updated_at']
            session.add(story_obj)

            for tag in bug['tags']:
                story_obj.tags.append(get_tag(tag, session))

            task_obj = Task()
            task_obj.assignee = get_user(task['assignee'], session)
            task_obj.created_at = bug['created_at']
            task_obj.creator = get_user(bug['creator'], session)
            task_obj.priority = bug['priority']
            task_obj.status = bug['status']
            task_obj.story = story_obj
            session.add(task_obj)

            for message in messages:
                comment_obj = Comment()
                comment_obj.content = message['content']
                comment_obj.created_at = message['created_at']
                session.add(comment_obj)
                timeline_obj = TimeLineEvent()
                timeline_obj.story = story_obj
                timeline_obj.comment = comment_obj
                timeline_obj.author = get_user(message['author'], session)
                timeline_obj.event_type = event_types.USER_COMMENT
                timeline_obj.created_at = message['created_at']
                session.add(timeline_obj)


def do_load_models(project):
    tasks = fetch_bugs(project)
    write_tasks(tasks)


def dump_tasks(tasks, outfile):
    json.dump(tasks, open(outfile, 'w'), sort_keys=True, indent=2)


def main():
    dump_tasks(fetch_bugs(sys.argv[1]), sys.argv[2])

if __name__ == '__main__':
    main()
