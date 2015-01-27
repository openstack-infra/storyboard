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


class TestBranches(base.FunctionalTest):
    def setUp(self):
        super(TestBranches, self).setUp()

        self.resource = '/branches'

        self.branch_01 = {
            'name': 'test_branch_01',
            'project_id': 1
        }

        self.branch_02 = {
            'name': 'test_branch_02',
            'project_id': 100
        }

        self.branch_03 = {
            'name': 'test_branch_03',
            'project_id': 1,
            'expiration_date': '2014-01-01T00:00:00+00:00'
        }

        self.put_branch_01 = {
            'project_id': 2
        }

        self.put_branch_02 = {
            'expired': True
        }

        self.put_branch_03 = {
            'expired': False
        }

        self.put_branch_04 = {
            'expired': False,
            'expiration_date': '2014-01-01T00:00:00+00:00'
        }

        self.project_01 = {
            'name': 'project-for-put',
            'description': 'test_description'
        }

        self.default_headers['Authorization'] = 'Bearer valid_superuser_token'

    def test_create(self):
        response = self.post_json(self.resource, self.branch_01)
        branch = response.json
        self.assertIn("id", branch)
        self.assertEqual(branch['name'], self.branch_01['name'])
        self.assertEqual(branch['project_id'], self.branch_01['project_id'])
        self.assertEqual(branch['expired'], False)
        self.assertIsNone(branch['expiration_date'])
        self.assertEqual(branch['autocreated'], False)

    def test_create_invalid(self):
        response = self.post_json(self.resource, self.branch_03,
                                  expect_errors=True)
        self.assertEqual(response.status_code, 400)

    def test_update(self):
        response = self.post_json(self.resource, self.branch_01)
        branch = response.json
        self.assertEqual(branch['name'], self.branch_01['name'])
        self.assertEqual(branch['project_id'], self.branch_01['project_id'])
        self.assertIn("id", branch)
        resource = "".join([self.resource, ("/%d" % branch['id'])])

        response_project = self.post_json('/projects', self.project_01)
        project = response_project.json

        self.assertEqual(self.project_01['name'], project['name'])
        self.assertEqual(self.project_01['description'],
                         project['description'])
        self.assertIn("id", project)
        self.put_branch_01["id"] = project["id"]

        response = self.put_json(resource, self.put_branch_01)
        branch = response.json
        self.assertEqual(branch['name'], self.branch_01['name'])
        self.assertEqual(branch['project_id'],
                         self.put_branch_01['project_id'])

        response = self.put_json(resource, self.put_branch_02)
        branch = response.json
        self.assertEqual(branch['expired'], True)
        self.assertIsNotNone(branch['expiration_date'])

        response = self.put_json(resource, self.put_branch_03)
        branch = response.json
        self.assertEqual(branch['expired'], False)
        self.assertIsNone(branch['expiration_date'])

    def test_update_expiration_date(self):
        response = self.post_json(self.resource, self.branch_01)
        branch = response.json
        self.assertEqual(branch['name'], self.branch_01['name'])
        self.assertEqual(branch['project_id'], self.branch_01['project_id'])
        self.assertIn("id", branch)
        resource = "".join([self.resource, ("/%d" % branch['id'])])

        response = self.put_json(resource, self.put_branch_02)
        branch = response.json
        self.assertEqual(branch['expired'], True)
        self.assertIsNotNone(branch['expiration_date'])

        response = self.put_json(resource, self.put_branch_04,
                                 expect_errors=True)
        self.assertEqual(response.status_code, 400)

    def test_get_one(self):
        response = self.post_json(self.resource, self.branch_01)
        branch = response.json
        resource = "".join([self.resource, ("/%d" % branch['id'])])

        branch = self.get_json(path=resource)
        self.assertEqual(branch['name'], self.branch_01['name'])
        self.assertEqual(branch['project_id'], self.branch_01['project_id'])
        self.assertEqual(branch['expired'], False)
        self.assertIsNone(branch['expiration_date'])
        self.assertEqual(branch['autocreated'], False)

    def test_get_invalid(self):
        resource = "".join([self.resource, "/1000"])
        response = self.get_json(path=resource, expect_errors=True)
        self.assertEqual(404, response.status_code)
