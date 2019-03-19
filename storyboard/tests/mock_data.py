# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
#
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

import datetime
import pytz

import storyboard.common.event_types as event
from storyboard.db.api import base as db
from storyboard.db.models import AccessToken
from storyboard.db.models import Branch
from storyboard.db.models import Comment
from storyboard.db.models import Milestone
from storyboard.db.models import Permission
from storyboard.db.models import Project
from storyboard.db.models import ProjectGroup
from storyboard.db.models import Story
from storyboard.db.models import Subscription
from storyboard.db.models import Task
from storyboard.db.models import Team
from storyboard.db.models import TimeLineEvent
from storyboard.db.models import User
from storyboard.db.models import UserPreference


def load():
    """Load a batch of useful data into the database that our tests can work
    with.
    """
    session = db.get_session(autocommit=False, in_request=False)
    now = datetime.datetime.now(tz=pytz.utc)
    expires_at = now + datetime.timedelta(seconds=3600)
    expired_at = now + datetime.timedelta(seconds=-3600)

    # Load users
    load_data([
        User(id=1,
             email='superuser@example.com',
             openid='superuser_openid',
             full_name='Super User',
             is_superuser=True),
        User(id=2,
             email='regularuser@example.com',
             openid='regularuser_openid',
             full_name='Regular User',
             is_superuser=False),
        User(id=3,
             email='otheruser@example.com',
             openid='otheruser_openid',
             full_name='Other User',
             is_superuser=False)
    ], session)
    users = session.query(User).all()

    # Load some preferences for the above users.
    load_data([
        UserPreference(id=1,
                       user_id=1,
                       key='foo',
                       value='bar',
                       type='string'),
        UserPreference(id=2,
                       user_id=1,
                       key='plugin_email_enable',
                       value='true',
                       type='string'),
        UserPreference(id=3,
                       user_id=1,
                       key='plugin_email_digest',
                       value='True',
                       type='bool'),
        UserPreference(id=4,
                       user_id=3,
                       key='plugin_email_enable',
                       value='true',
                       type='string'),
        UserPreference(id=5,
                       user_id=3,
                       key='plugin_email_digest',
                       value='False',
                       type='bool'),
    ], session)

    # Load a variety of sensibly named access tokens.
    load_data([
        AccessToken(
            user_id=1,
            access_token='valid_superuser_token',
            expires_in=3600,
            expires_at=expires_at),
        AccessToken(
            user_id=1,
            access_token='expired_superuser_token',
            expires_in=3600,
            expires_at=expired_at),
        AccessToken(
            user_id=2,
            access_token='valid_user_token',
            expires_in=3600,
            expires_at=expires_at),
        AccessToken(
            user_id=2,
            access_token='expired_user_token',
            expires_in=3600,
            expires_at=expired_at)
    ], session)

    # Create some test projects.
    projects = load_data([
        Project(
            id=1,
            name='project1',
            description='Project 3 Description - foo'),
        Project(
            id=2,
            name='project2',
            description='Project 2 Description - bar'),
        Project(
            id=3,
            name='tests/project3',
            description='Project 1 Description - foo')
    ], session)

    # Create some test project groups.
    load_data([
        ProjectGroup(
            id=1,
            name='projectgroup1',
            title='C Sort - foo',
            projects=[
                projects[0],
                projects[2]
            ]
        ),
        ProjectGroup(
            id=2,
            name='projectgroup2',
            title='B Sort - bar',
            projects=[
                projects[1],
                projects[2]
            ]
        ),
        ProjectGroup(
            id=3,
            name='projectgroup3',
            title='A Sort - foo'
        )
    ], session)

    # Create some permissions
    load_data([
        Permission(
            name='view_story_6',
            codename='view_story',
            users=[users[0]]
        )
    ], session)
    permissions = session.query(Permission).all()

    # Create some stories.
    load_data([
        Story(
            id=1,
            title="E Test story 1 - foo",
            description="Test Description - foo"
        ),
        Story(
            id=2,
            title="D Test story 2 - bar",
            description="Test Description - bar"
        ),
        Story(
            id=3,
            title="C Test story 3 - foo",
            description="Test Description - foo"
        ),
        Story(
            id=4,
            title="B Test story 4 - bar",
            description="Test Description - bar"
        ),
        Story(
            id=5,
            title="A Test story 5 - oh hai",
            description="Test Description - oh hai"
        ),
        Story(
            id=6,
            title="Test Private Story",
            description="For Super User's eyes only",
            private=True,
            permissions=[permissions[0]]
        )
    ], session)

    # Create some tasks
    load_data([
        Task(
            id=1,
            creator_id=1,
            title='A Test Task 1 - foo',
            status='inprogress',
            story_id=1,
            project_id=1,
            branch_id=1,
            assignee_id=2,
            priority='medium'
        ),
        Task(
            id=2,
            creator_id=1,
            title='B Test Task 2 - bar',
            status='merged',
            story_id=1,
            project_id=2,
            branch_id=2,
            assignee_id=1,
            priority='high'
        ),
        Task(
            id=3,
            creator_id=1,
            title='C Test Task 3 - foo',
            status='invalid',
            story_id=1,
            project_id=3,
            branch_ud=3,
            assignee_id=1,
            priority='low'
        ),
        Task(
            id=4,
            creator_id=1,
            title='D Test Task 4 - bar',
            status='merged',
            story_id=2,
            project_id=2,
            branch_id=2,
            assignee_id=1,
            priority='medium'
        ),
        Task(
            id=5,
            creator_id=1,
            title='Task in private story',
            status='todo',
            story_id=6,
            project_id=2,
            branch_id=2,
            assignee_id=1,
            priority='medium'
        )
    ], session)

    # Generate some timeline events for the above stories.
    load_data([
        TimeLineEvent(
            id=1,
            story_id=1,
            author_id=1,
            event_type=event.STORY_CREATED,
            event_info='{"story_id": 1, "story_title": "E Test story 1 - foo"}'
        ),
        TimeLineEvent(
            id=2,
            story_id=2,
            author_id=1,
            event_type=event.STORY_CREATED,
            event_info='{"story_id": 1, "story_title": "D Test story 2 - bar"}'
        ),
        TimeLineEvent(
            id=3,
            story_id=3,
            author_id=1,
            event_type=event.STORY_CREATED,
            event_info='{"story_id": 1, "story_title": "C Test story 3 - foo"}'
        ),
        TimeLineEvent(
            id=4,
            story_id=4,
            author_id=1,
            event_type=event.STORY_CREATED,
            event_info='{"story_id": 1, "story_title": "B Test story 4 - bar"}'
        ),
        TimeLineEvent(
            id=5,
            story_id=5,
            author_id=1,
            event_type=event.STORY_CREATED,
            event_info='{"story_id": 1, '
                       '"story_title": "A Test story 5 - oh hai"}'
        ),
        # Reassign task 1 to user 2.
        TimeLineEvent(
            id=6,
            story_id=1,
            author_id=1,
            event_type=event.TASK_ASSIGNEE_CHANGED,
            event_info='{"story_id": 1, "task_title": "A Test Task 1 - foo", '
                       '"old_assignee_id": null, '
                       '"task_id": 1, '
                       '"new_assignee_id": 2}'
        ),
        TimeLineEvent(
            id=7,
            story_id=6,
            author_id=1,
            event_type=event.STORY_CREATED,
            event_info='{"story_id": 6, '
                       '"story_title": "Test Private Story"}'
        )
    ], session)

    # Create some comments.
    load_data([
        Comment(
            id=1,
            content="Test Comment",
            is_active=True
        ),
        Comment(
            id=2,
            content="Comment on a private story",
            is_active=True
        )
    ], session)

    # Create timeline events for the above comments.
    load_data([
        TimeLineEvent(
            id=8,
            story_id=1,
            comment_id=1,
            author_id=1,
            event_type=event.USER_COMMENT
        ),
        TimeLineEvent(
            id=9,
            story_id=6,
            comment_id=2,
            author_id=1,
            event_type=event.USER_COMMENT
        )
    ], session)

    # Load some subscriptions.
    load_data([
        Subscription(
            id=1,
            user_id=1,
            target_type='project_group',
            target_id=1
        ),
        Subscription(
            id=2,
            user_id=1,
            target_type='project',
            target_id=3
        ),
        Subscription(
            id=3,
            user_id=3,
            target_type='story',
            target_id=1
        ),
    ], session)

    # Load some branches
    load_data([
        Branch(
            id=1,
            project_id=1,
            name='master',
            restricted=True
        ),
        Branch(
            id=2,
            project_id=2,
            name='master',
            restricted=True
        ),
        Branch(
            id=3,
            project_id=3,
            name='master',
            restricted=True
        )
    ], session)

    # Load some milestones
    load_data([
        Milestone(
            id=1,
            name='test_milestone_01',
            branch_id=1
        ),
        Milestone(
            id=2,
            name='test_milestone_02',
            branch_id=2
        )
    ], session)

    # Load some teams
    load_data([
        Team(
            id=1,
            name='test_team_1',
            users=[users[0]]
        ),
        Team(
            id=2,
            name='test_team_2',
            users=users[1:]
        )
    ], session)


def load_data(data, session=None):
    """Pre load test data into the database.

    :param data An iterable collection of database models.
    """
    if session is None:
        session = db.get_session(autocommit=False, in_request=False)

    for entity in data:
        session.add(entity)

    session.commit()

    # Clear these items from the session.
    for entity in data:
        session.expunge(entity)

    return data
