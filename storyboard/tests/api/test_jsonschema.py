# Copyright (c) 2014 Mirantis Inc.
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

import six

from storyboard.tests import base


LONG_STRING = ''.join(['a' for i in range(0, 260)])


def create(test_class, entity, resource):
    response_body = test_class.post_json(resource, entity).json

    for key, value in six.iteritems(entity):
        test_class.assertEqual(value, response_body[key])


def create_invalid_length(test_class, entity, resource, field=""):
    response = test_class.post_json(resource, entity, expect_errors=True)
    response_body = response.json
    test_class.assertEqual(400, response.status_code)
    test_class.assertEqual(field, response_body["field"])


def create_invalid_required(test_class, entity, resource, field=""):
    response = test_class.post_json(resource, entity, expect_errors=True)
    response_body = response.json
    test_class.assertEqual(400, response.status_code)
    test_class.assertEqual(six.text_type('\'%s\' is a required property') %
                           field, response_body["message"])


def update(test_class, entity, resource):
    response = test_class.put_json(resource, entity)
    response_body = response.json

    for key, value in six.iteritems(entity):
        test_class.assertEqual(value, response_body[key])


def update_invalid(test_class, entity, resource, field=""):
    response = test_class.put_json(resource, entity, expect_errors=True)
    response_body = response.json
    test_class.assertEqual(400, response.status_code)
    test_class.assertEqual(field, response_body["field"])


class TestUsers(base.FunctionalTest):
    def setUp(self):
        super(TestUsers, self).setUp()

        self.resource = '/users'
        self.default_headers['Authorization'] = 'Bearer valid_superuser_token'

        self.user_01 = {
            'full_name': 'jsonschema_test_user1',
            'email': 'jsonschema_test_user1@test.ru',
            'openid': 'qwerty'
        }

        self.user_02 = {
            'full_name': LONG_STRING,
            'email': 'jsonschema_test_user3@test.ru',
            'openid': 'qwertyui'
        }

        self.user_03 = {
            'username': 'jsonschema_test_user3',
            'full_name': LONG_STRING,
            'email': 'jsonschema_test_user3@test.ru',
            'openid': 'qwertyui'
        }

        self.put_user_01 = {
            'full_name': 'new full_name of regular User'
        }

        self.put_user_02 = {
            'full_name': 'ok'
        }

        self.put_user_03 = {
            'email': LONG_STRING
        }

    def test_create(self):
        create(self, self.user_01, self.resource)

    def test_create_invalid(self):
        create_invalid_length(self, self.user_02, self.resource, 'full_name')

    def test_update(self):
        resource = "".join([self.resource, "/2"])
        update(self, self.put_user_01, resource)

    def test_update_invalid(self):
        resource = "".join([self.resource, "/2"])
        update_invalid(self, self.put_user_02, resource, 'full_name')
        update_invalid(self, self.put_user_03, resource, 'email')


class TestProjects(base.FunctionalTest):
    def setUp(self):
        super(TestProjects, self).setUp()

        self.resource = '/projects'
        self.default_headers['Authorization'] = 'Bearer valid_superuser_token'

        self.project_01 = {
            'name': 'jsonschema-project-01',
            'description': 'jsonschema_description_01'
        }

        self.project_02 = {
            'name': 'pr',
            'description': 'jsonschema_description_02'
        }

        self.project_03 = {
            'name': LONG_STRING,
            'description': 'jsonschema_description_03'
        }

        self.project_04 = {
            'description': 'jsonschema_description_04'
        }

        self.put_project_01 = {
            'id': 2,
            'description': 'jsonschema_put_description_01'
        }

        self.put_project_02 = {
            'name': 'ok'
        }

        self.put_project_03 = {
            'name': LONG_STRING
        }

    def test_create(self):
        create(self, self.project_01, self.resource)

    def test_create_invalid(self):
        create_invalid_length(self, self.project_02, self.resource, 'name')
        create_invalid_length(self, self.project_03, self.resource, 'name')
        create_invalid_required(self, self.project_04, self.resource, 'name')

    def test_update(self):
        resource = "".join([self.resource, "/2"])
        update(self, self.put_project_01, resource)

    def test_update_invalid(self):
        resource = "".join([self.resource, "/2"])
        update_invalid(self, self.put_project_02, resource, 'name')
        update_invalid(self, self.put_project_03, resource, 'name')


class TestUserPreferences(base.FunctionalTest):
    def setUp(self):
        super(TestUserPreferences, self).setUp()

        self.resource = '/users/2/preferences'
        self.default_headers['Authorization'] = 'Bearer valid_user_token'

        self.preferences_01 = {
            'stringPref': 'jsonschema_preference_01'
        }

        self.preferences_02 = {
            'stringPref': ''
        }

        self.preferences_03 = {
            'stringPref': LONG_STRING
        }

    def test_create(self):
        create(self, self.preferences_01, self.resource)

    def test_create_invalid(self):
        create_invalid_length(self, self.preferences_02, self.resource,
                              'stringPref')
        create_invalid_length(self, self.preferences_03, self.resource,
                              'stringPref')


class TestTeams(base.FunctionalTest):
    def setUp(self):
        super(TestTeams, self).setUp()

        self.resource = '/teams'
        self.default_headers['Authorization'] = 'Bearer valid_superuser_token'

        self.team_01 = {
            'name': 'jsonschema-team-01'
        }

        self.team_02 = {
            'name': 'te'
        }

        self.team_03 = {
            'name': LONG_STRING
        }

        self.team_04 = {
        }

    def test_create(self):
        create(self, self.team_01, self.resource)

    def test_create_invalid(self):
        create_invalid_length(self, self.team_02, self.resource,
                              'name')
        create_invalid_length(self, self.team_03, self.resource,
                              'name')
        create_invalid_required(self, self.team_04, self.resource, 'name')


class TestProjectGroups(base.FunctionalTest):
    def setUp(self):
        super(TestProjectGroups, self).setUp()

        self.resource = '/project_groups'
        self.default_headers['Authorization'] = 'Bearer valid_superuser_token'

        self.project_group_01 = {
            'name': 'jsonschema-project-group-01',
            'title': 'jsonschema_project_group_title_01'
        }

        self.project_group_02 = {
            'name': 'pr',
            'title': 'jsonschema_project_group_title_02'
        }

        self.project_group_03 = {
            'name': 'jsonschema-project-group-03',
            'title': LONG_STRING
        }

        self.project_group_04 = {
            'name': 'jsonschema-project-group-04',
        }

        self.put_project_group_01 = {
            'title': 'put_project_group_01'
        }

        self.put_project_group_02 = {
            'title': 'tl'
        }

        self.put_project_group_03 = {
            'title': LONG_STRING
        }

    def test_create(self):
        create(self, self.project_group_01, self.resource)

    def test_create_invalid(self):
        create_invalid_length(self, self.project_group_02, self.resource,
                              'name')
        create_invalid_length(self, self.project_group_03, self.resource,
                              'title')
        create_invalid_required(self, self.project_group_04, self.resource,
                                'title')

    def test_update(self):
        resource = "".join([self.resource, "/2"])
        update(self, self.put_project_group_01, resource)

    def test_update_invalid(self):
        resource = "".join([self.resource, "/2"])
        update_invalid(self, self.put_project_group_02, resource, 'title')
        update_invalid(self, self.put_project_group_03, resource, 'title')


class TestStories(base.FunctionalTest):
    def setUp(self):
        super(TestStories, self).setUp()

        self.resource = '/stories'
        self.default_headers['Authorization'] = 'Bearer valid_superuser_token'

        self.story_01 = {
            'title': 'jsonschema_story_01',
            'description': 'jsonschema_story_description_01'
        }

        self.story_02 = {
            'title': 'st',
            'description': 'jsonschema_story_description_02'
        }

        self.story_03 = {
            'title': LONG_STRING,
            'description': 'jsonschema_story_description_03'
        }

        self.story_04 = {
            'description': 'jsonschema_story_description_04'
        }

        self.put_story_01 = {
            'title': 'put_story_01'
        }

        self.put_story_02 = {
            'title': 'tl'
        }

        self.put_story_03 = {
            'title': LONG_STRING
        }

    def test_create(self):
        create(self, self.story_01, self.resource)

    def test_create_invalid(self):
        create_invalid_length(self, self.story_02, self.resource,
                              'title')
        create_invalid_length(self, self.story_03, self.resource,
                              'title')
        create_invalid_required(self, self.story_04, self.resource,
                                'title')

    def test_update(self):
        resource = "".join([self.resource, "/2"])
        update(self, self.put_story_01, resource)

    def test_update_invalid(self):
        resource = "".join([self.resource, "/2"])
        update_invalid(self, self.put_story_02, resource, 'title')
        update_invalid(self, self.put_story_03, resource, 'title')


class TestTasks(base.FunctionalTest):
    def setUp(self):
        super(TestTasks, self).setUp()

        self.resource = '/tasks'
        self.default_headers['Authorization'] = 'Bearer valid_superuser_token'

        self.task_01 = {
            'title': 'jsonschema_task_01',
            'story_id': 1,
            'project_id': 1
        }

        self.task_02 = {
            'title': 'ts',
            'story_id': 1,
            'project_id': 1
        }

        self.task_03 = {
            'title': LONG_STRING,
            'story_id': 1,
            'project_id': 1
        }

        self.task_04 = {
            'story_id': 1,
            'project_id': 1
        }

        self.put_task_01 = {
            'title': 'put_task_01'
        }

        self.put_task_02 = {
            'title': 'tl'
        }

        self.put_task_03 = {
            'title': LONG_STRING
        }

    def test_create(self):
        create(self, self.task_01, self.resource)

    def test_create_invalid(self):
        create_invalid_length(self, self.task_02, self.resource,
                              'title')
        create_invalid_length(self, self.task_03, self.resource,
                              'title')
        create_invalid_required(self, self.task_04, self.resource,
                                'title')

    def test_update(self):
        resource = "".join([self.resource, "/2"])
        update(self, self.put_task_01, resource)

    def test_update_invalid(self):
        resource = "".join([self.resource, "/2"])
        update_invalid(self, self.put_task_02, resource, 'title')
        update_invalid(self, self.put_task_03, resource, 'title')
