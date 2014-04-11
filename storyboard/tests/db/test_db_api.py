# Copyright (c) 2014 Mirantis Inc.
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

from datetime import datetime

from storyboard.db.api import auth
from storyboard.db.api import comments
from storyboard.db.api import projects
from storyboard.db.api import stories
from storyboard.db.api import tasks
from storyboard.tests import base


class BaseDbTestCase(base.DbTestCase):
    def setUp(self):
        super(BaseDbTestCase, self).setUp()

    def _assert_saved_fields(self, expected, actual):
        for k in expected.keys():
            self.assertEqual(expected[k], actual[k])

    def _test_create(self, ref, save_method):
        saved = save_method(ref)

        self.assertIsNotNone(saved.id)
        self._assert_saved_fields(ref, saved)

    def _test_update(self, ref, delta, create, update):
        saved = create(ref)
        updated = update(saved.id, delta)

        self.assertEqual(saved.id, updated.id)
        self._assert_saved_fields(delta, updated)


class ProjectsTest(BaseDbTestCase):

    def setUp(self):
        super(ProjectsTest, self).setUp()

        self.project_01 = {
            'name': u'StoryBoard',
            'description': u'Awesome Task Tracker'
        }

    def test_save_project(self):
        self._test_create(self.project_01, projects.project_create)

    def test_update_project(self):
        delta = {
            'name': u'New Name',
            'description': u'New Description'
        }
        self._test_update(self.project_01, delta,
                          projects.project_create, projects.project_update)


class StoriesTest(BaseDbTestCase):

    def setUp(self):
        super(StoriesTest, self).setUp()

        self.story_01 = {
            'title': u'Worst Story Ever',
            'description': u'Story description'
        }

    def test_create_story(self):
        self._test_create(self.story_01, stories.story_create)

    def test_update_story(self):
        delta = {
            'title': u'New Title',
            'description': u'New Description'
        }
        self._test_update(self.story_01, delta,
                          stories.story_create, stories.story_update)


class TasksTest(BaseDbTestCase):

    def setUp(self):
        super(TasksTest, self).setUp()

        self.task_01 = {
            'title': u'Invent time machine',
            'status': 'todo',
            'story_id': 1
        }

    def test_create_task(self):
        self._test_create(self.task_01, tasks.task_create)

    def test_update_task(self):
        delta = {
            'status': 'review',
            'assignee_id': 1
        }

        self._test_update(self.task_01, delta,
                          tasks.task_create, tasks.task_update)


class CommentsTest(BaseDbTestCase):

    def setUp(self):
        super(CommentsTest, self).setUp()

        self.comment_01 = {
            'content': u'A comment',
            'story_id': 1
        }

    def test_create_comment(self):
        self._test_create(self.comment_01, comments.comment_create)

    def test_update_comment(self):
        delta = {
            'content': u'An updated comment'
        }

        self._test_update(self.comment_01, delta,
                          comments.comment_create, comments.comment_update)


class AuthorizationCodeTest(BaseDbTestCase):

    def setUp(self):
        super(AuthorizationCodeTest, self).setUp()

        self.code_01 = {
            'code': u'some_random_stuff',
            'state': u'another_random_stuff',
            'user_id': 1
        }

    def test_create_code(self):
        self._test_create(self.code_01, auth.authorization_code_save)

    def test_delete_code(self):
        created_code = auth.authorization_code_save(self.code_01)

        self.assertIsNotNone(created_code,
                             "Could not create an Authorization code")

        auth.authorization_code_delete(created_code.code)

        fetched_code = auth.authorization_code_get(created_code.code)
        self.assertIsNone(fetched_code)


class TokenTest(BaseDbTestCase):

    def setUp(self):
        super(TokenTest, self).setUp()

        self.token_01 = {
            "access_token": u'an_access_token',
            "refresh_token": u'a_refresh_token',
            "expires_in": 3600,
            "expires_at": datetime.now(),
            "user_id": 1
        }

    def test_create_token(self):
        self._test_create(self.token_01, auth.access_token_save)

    def test_delete_token(self):
        created_token = auth.access_token_save(self.token_01)

        self.assertIsNotNone(created_token, "Could not create a Token")

        auth.access_token_delete(created_token.access_token)

        fetched_token = auth.access_token_get(created_token.access_token)
        self.assertIsNone(fetched_token, "A deleted token was fetched.")
