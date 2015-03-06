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


class TestMilestones(base.FunctionalTest):
    def setUp(self):
        super(TestMilestones, self).setUp()

        self.resource = '/milestones'

        self.milestone_01 = {
            'name': 'test_milestone_1',
            'branch_id': 1
        }

        self.milestone_02 = {
            'name': 'test_milestone_02',
            'branch_id': 100
        }

        self.milestone_03 = {
            'name': 'test_milestone_03',
            'branch_id': 1,
            'expiration_date': '2014-01-01T00:00:00+00:00'
        }

        self.put_milestone_01 = {
            'name': 'new_milestone_name'
        }

        self.put_milestone_02 = {
            'expired': True
        }

        self.put_milestone_03 = {
            'expired': False
        }

        self.put_milestone_04 = {
            'expired': False,
            'expiration_date': '2014-01-01T00:00:00+00:00'
        }

        self.default_headers['Authorization'] = 'Bearer valid_superuser_token'

    def test_create(self):
        response = self.post_json(self.resource, self.milestone_01)
        milestone = response.json
        self.assertIn("id", milestone)
        self.assertEqual(milestone['name'], self.milestone_01['name'])
        self.assertEqual(milestone['branch_id'],
                         self.milestone_01['branch_id'])
        self.assertEqual(milestone['expired'], False)
        self.assertIsNone(milestone['expiration_date'])

    def test_create_invalid(self):
        response = self.post_json(self.resource, self.milestone_03,
                                  expect_errors=True)

        self.assertEqual(response.status_code, 400)

    def test_update(self):
        response = self.post_json(self.resource, self.milestone_01)
        milestone = response.json
        self.assertEqual(milestone['name'], self.milestone_01['name'])
        self.assertEqual(milestone['branch_id'],
                         self.milestone_01['branch_id'])
        self.assertIn("id", milestone)
        resource = "".join([self.resource, ("/%d" % milestone['id'])])

        response = self.put_json(resource, self.put_milestone_01)
        milestone = response.json
        self.assertEqual(milestone['name'], self.put_milestone_01['name'])
        self.assertEqual(milestone['branch_id'],
                         self.milestone_01['branch_id'])

        response = self.put_json(resource, self.put_milestone_02)
        milestone = response.json
        self.assertEqual(milestone['expired'], True)
        self.assertIsNotNone(milestone['expiration_date'])

        response = self.put_json(resource, self.put_milestone_03)
        milestone = response.json
        self.assertEqual(milestone['expired'], False)
        self.assertIsNone(milestone['expiration_date'])

    def test_update_expiration_date(self):
        response = self.post_json(self.resource, self.milestone_01)
        milestone = response.json
        self.assertEqual(milestone['name'], self.milestone_01['name'])
        self.assertEqual(milestone['branch_id'],
                         self.milestone_01['branch_id'])
        self.assertIn("id", milestone)
        resource = "".join([self.resource, ("/%d" % milestone['id'])])

        response = self.put_json(resource, self.put_milestone_02)
        milestone = response.json
        self.assertEqual(milestone['expired'], True)
        self.assertIsNotNone(milestone['expiration_date'])

        response = self.put_json(resource, self.put_milestone_04,
                                 expect_errors=True)
        self.assertEqual(response.status_code, 400)

    def test_change_branch(self):
        response = self.post_json(self.resource, self.milestone_01)
        milestone = response.json
        self.assertIn("id", milestone)
        self.assertEqual(milestone['name'], self.milestone_01['name'])
        self.assertEqual(milestone['branch_id'],
                         self.milestone_01['branch_id'])
        resource = "".join([self.resource, ("/%d" % milestone['id'])])

        response = self.put_json(resource, {'branch_id': 2},
                                 expect_errors=True)
        self.assertEqual(400, response.status_code)

    def test_get_one(self):
        response = self.post_json(self.resource, self.milestone_01)
        milestone = response.json
        resource = "".join([self.resource, ("/%d" % milestone['id'])])

        milestone = self.get_json(path=resource)
        self.assertEqual(milestone['name'], self.milestone_01['name'])
        self.assertEqual(milestone['branch_id'],
                         self.milestone_01['branch_id'])
        self.assertEqual(milestone['expired'], False)
        self.assertIsNone(milestone['expiration_date'])

    def test_get_invalid(self):
        resource = "".join([self.resource, "/1000"])
        response = self.get_json(path=resource, expect_errors=True)
        self.assertEqual(404, response.status_code)
