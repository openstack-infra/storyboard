# Copyright (c) 2015 Mirantis Inc.
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

from storyboard.tests import base


class TestDBExceptions(base.FunctionalTest):
    def setUp(self):
        super(TestDBExceptions, self).setUp()
        self.default_headers['Authorization'] = 'Bearer valid_superuser_token'

    # test duplicate entry error
    # in this test we try to create two equal projects
    def test_duplicate_project_create(self):
        resource = '/projects'
        project = {
            'name': 'test-project-duplicate',
            'description': 'test_project_duplicate_description',
        }

        # create project with name 'test-project-duplicate'
        response = self.post_json(resource, project)
        body = response.json
        self.assertEqual(project['name'], body['name'])
        self.assertEqual(project['description'], body['description'])

        # repeat creating this project
        # because project with name 'test-project-duplicate' already exists, we
        # wait abort with code_status 400
        response = self.post_json(resource, project, expect_errors=True)
        self.assertEqual(400, response.status_code)

    # test duplicate entry error
    # in this test we try to create two equal users
    def test_duplicate_user_create(self):
        # send user first time
        resource = '/users'
        user = {
            'full_name': 'Test duplicate',
            'email': 'dupe@example.com'
        }

        response = self.post_json(resource, user)
        users_body = response.json
        self.assertEqual(user['full_name'], users_body['full_name'])
        self.assertEqual(user['email'], users_body['email'])

        # send user again
        response = self.post_json(resource, user, expect_errors=True)
        self.assertEqual(400, response.status_code)
