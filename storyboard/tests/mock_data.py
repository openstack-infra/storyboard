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

from storyboard.db.api import base as db
from storyboard.db.models import AccessToken
from storyboard.db.models import Project
from storyboard.db.models import ProjectGroup
from storyboard.db.models import Story
from storyboard.db.models import Task
from storyboard.db.models import User


def load():
    """Load a batch of useful data into the database that our tests can work
    with.
    """
    now = datetime.datetime.now()
    expires_at = now + datetime.timedelta(seconds=3600)
    expired_at = now + datetime.timedelta(seconds=-3600)

    # Load users
    load_data([
        User(id=1,
             username='superuser',
             email='superuser@example.com',
             full_name='Super User',
             is_superuser=True),
        User(id=2,
             username='regularuser',
             email='regularuser@example.com',
             full_name='Regular User',
             is_superuser=False)
    ])

    # Load a variety of sensibly named access tokens.
    load_data([
        AccessToken(
            user_id=1,
            access_token='valid_superuser_token',
            expires_in=3600,
            expires_at=expires_at.strftime('%Y-%m-%d %H:%M:%S')),
        AccessToken(
            user_id=1,
            access_token='expired_superuser_token',
            expires_in=3600,
            expires_at=expired_at.strftime('%Y-%m-%d %H:%M:%S')),
        AccessToken(
            user_id=2,
            access_token='valid_user_token',
            expires_in=3600,
            expires_at=expires_at.strftime('%Y-%m-%d %H:%M:%S')),
        AccessToken(
            user_id=2,
            access_token='expired_user_token',
            expires_in=3600,
            expires_at=expired_at.strftime('%Y-%m-%d %H:%M:%S'))
    ])

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
            name='project3',
            description='Project 1 Description - foo')
    ])

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
    ])

    # Create some stories.
    load_data([
        Story(
            id=1,
            title="Test story 1 - foo"
        ),
        Story(
            id=2,
            title="Test story 2 - bar"
        ),
        Story(
            id=3,
            title="Test story 3 - foo"
        ),
        Story(
            id=4,
            title="Test story 4 - bar"
        ),
        Story(
            id=5,
            title="Test story 5 - oh hai"
        )
    ])

    # Create some tasks
    load_data([
        Task(
            id=1,
            creator_id=1,
            title='A Test Task 1 - foo',
            status='inprogress',
            story_id=1,
            project_id=1,
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
            assignee_id=1,
            priority='medium'
        )
    ])


def load_data(data):
    """Pre load test data into the database.

    :param data An iterable collection of database models.
    """
    session = db.get_session(autocommit=False)

    for entity in data:
        session.add(entity)

    session.commit()

    # Clear these items from the session.
    for entity in data:
        session.expunge(entity)

    return data
