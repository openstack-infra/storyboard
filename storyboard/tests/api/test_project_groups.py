# Copyright (c) 2014 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import json

from webtest.app import AppError

from storyboard.tests import base


class TestProjectGroups(base.FunctionalTest):

    def setUp(self):
        super(TestProjectGroups, self).setUp()

        self.resource = '/project_groups'

        self.group_01 = {
            'name': 'test-group',
            'title': 'with a title'
        }

    def test_projects_endpoint(self):
        response = self.get_json(path=self.resource)
        self.assertEqual([], response)

    def test_create(self):

        response = self.post_json(self.resource, self.group_01)
        project_group = json.loads(response.body)

        self.assertEqual(self.group_01['name'], project_group['name'])
        self.assertEqual(self.group_01['title'], project_group['title'])

    def test_create_invalid(self):

        invalid_project_group = self.group_01.copy()
        invalid_project_group["name"] = "name with spaces"

        self.assertRaises(AppError, self.post_json, self.resource,
                          invalid_project_group)

    def test_update(self):
        response = self.post_json(self.resource, self.group_01)
        original = json.loads(response.body)

        delta = {
            'id': original['id'],
            'name': 'new-name',
            'title': 'new title'
        }

        url = "/project_groups/%d" % original['id']
        response = self.put_json(url, delta)
        updated = json.loads(response.body)

        self.assertEqual(original['id'], updated['id'])

        self.assertNotEqual(original['name'], updated['name'])
        self.assertNotEqual(original['title'], updated['title'])

    def test_update_invalid(self):
        response = self.post_json(self.resource, self.group_01)
        original = json.loads(response.body)

        delta = {
            'id': original['id'],
            'name': 'new-name is invalid!',
        }

        url = "/project_groups/%d" % original['id']

        # check for invalid characters like space and '!'
        self.assertRaises(AppError, self.put_json, url, delta)

        delta["name"] = "a"

        # check for a too short name
        self.assertRaises(AppError, self.put_json, url, delta)
