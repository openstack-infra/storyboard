# Copyright (c) 2013 Mirantis Inc.
# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
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
from urllib import urlencode

from webtest.app import AppError

from storyboard.db.models import Project
from storyboard.db.models import ProjectGroup
from storyboard.db.models import User
from storyboard.tests import base


class TestProjects(base.FunctionalTest):

    def setUp(self):
        super(TestProjects, self).setUp()

        self.resource = '/projects'

        self.project_01 = {
            'name': 'test-project',
            'description': 'some description'
        }

        self.load_data([
            User(id=1,
                 username='superuser',
                 email='superuser@example.com',
                 full_name='Super User',
                 is_superuser=True),
            Project(id=1,
                    name='test-project-1',
                    description='Test Project Description')
        ])
        su_token = self.build_access_token(1)
        self.default_headers['Authorization'] = 'Bearer %s' % (
            su_token.access_token)

    def test_projects_endpoint(self):
        response = self.get_json(path=self.resource)
        self.assertEqual(1, len(response))

    def test_get(self):
        response = self.get_json(path=self.resource + "/1")
        self.assertEqual(1, response['id'])
        self.assertEqual('test-project-1', response['name'])
        self.assertEqual('Test Project Description', response['description'])

    def test_get_nonexistent(self):
        response = self.get_json(path=self.resource + "/999",
                                 expect_errors=True)
        self.assertEqual(404, response.status_code)

    def test_create(self):

        response = self.post_json(self.resource, self.project_01)
        project = json.loads(response.body)

        self.assertEqual(self.project_01['name'], project['name'])
        self.assertEqual(self.project_01['description'],
                         project['description'])

    def test_create_invalid(self):

        invalid_project = self.project_01.copy()
        invalid_project["name"] = "name with spaces"

        self.assertRaises(AppError, self.post_json, self.resource,
                          invalid_project)

    def test_update(self):
        response = self.post_json(self.resource, self.project_01)
        original = json.loads(response.body)

        delta = {
            'id': original['id'],
            'name': 'new-name',
            'description': 'new description'
        }

        url = "/projects/%d" % original['id']
        response = self.put_json(url, delta)
        updated = json.loads(response.body)

        self.assertEqual(original['id'], updated['id'])

        self.assertNotEqual(original['name'], updated['name'])
        self.assertNotEqual(original['description'],
                            updated['description'])

    def test_update_invalid(self):
        response = self.post_json(self.resource, self.project_01)
        original = json.loads(response.body)

        delta = {
            'id': original['id'],
            'name': 'new-name is invalid!',
        }

        url = "/projects/%d" % original['id']

        # check for invalid characters like space and '!'
        self.assertRaises(AppError, self.put_json, url, delta)

        delta["name"] = "a"

        # check for a too short name
        self.assertRaises(AppError, self.put_json, url, delta)


class TestProjectSearch(base.FunctionalTest):
    def setUp(self):
        super(TestProjectSearch, self).setUp()

        projects = self.load_data([
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

        self.load_data([
            ProjectGroup(
                id=1,
                name='projectgroup1',
                title='Project Group 1',
                projects=[
                    projects[0],
                    projects[2]
                ]
            ),
            ProjectGroup(
                id=2,
                name='projectgroup2',
                title='Project Group 2',
                projects=[
                    projects[1],
                    projects[2]
                ]
            )
        ])

    def build_search_url(self, params):
        return '/projects?%s' % (urlencode(params))

    def test_search(self):
        url = self.build_search_url({
        })

        results = self.get_json(url, expect_errors=True)
        self.assertEqual(3, len(results.json))
        self.assertEqual('3', results.headers['X-Total'])
        self.assertFalse('X-Marker' in results.headers)

    def test_search_by_name(self):
        url = self.build_search_url({
            'name': 'project1'
        })

        results = self.get_json(url, expect_errors=True)
        self.assertEqual(1, len(results.json))
        self.assertEqual('1', results.headers['X-Total'])
        self.assertFalse('X-Marker' in results.headers)

        result = results.json[0]
        self.assertEqual('project1', result['name'])

    def test_search_by_description(self):
        url = self.build_search_url({
            'description': 'foo'
        })

        results = self.get_json(url, expect_errors=True)
        self.assertEqual(2, len(results.json))
        self.assertEqual('2', results.headers['X-Total'])
        self.assertFalse('X-Marker' in results.headers)

        result = results.json[0]
        self.assertEqual(1, result['id'])
        result = results.json[1]
        self.assertEqual(3, result['id'])

    def test_search_limit(self):
        url = self.build_search_url({
            'description': 'foo',
            'limit': 1
        })

        results = self.get_json(url, expect_errors=True)
        self.assertEqual(1, len(results.json))
        self.assertEqual('2', results.headers['X-Total'])
        self.assertEqual('1', results.headers['X-Limit'])
        self.assertFalse('X-Marker' in results.headers)

        result = results.json[0]
        self.assertEqual(1, result['id'])

    def test_search_marker(self):
        url = self.build_search_url({
            'description': 'foo',
            'marker': 1  # Last item in previous list.
        })

        results = self.get_json(url, expect_errors=True)
        self.assertEqual(1, len(results.json))
        self.assertEqual('2', results.headers['X-Total'])
        self.assertEqual('1', results.headers['X-Marker'])

        result = results.json[0]
        self.assertEqual(3, result['id'])

    def test_search_direction(self):
        url = self.build_search_url({
            'sort_field': 'description',
            'sort_dir': 'asc'
        })

        results = self.get_json(url, expect_errors=True)
        self.assertEqual(3, len(results.json))
        self.assertEqual('3', results.headers['X-Total'])
        self.assertFalse('X-Marker' in results.headers)

        result = results.json[0]
        self.assertEqual(3, result['id'])
        result = results.json[1]
        self.assertEqual(2, result['id'])
        result = results.json[2]
        self.assertEqual(1, result['id'])

    def test_search_direction_desc(self):
        url = self.build_search_url({
            'sort_field': 'description',
            'sort_dir': 'desc'
        })

        results = self.get_json(url, expect_errors=True)
        self.assertEqual(3, len(results.json))
        self.assertEqual('3', results.headers['X-Total'])
        self.assertFalse('X-Marker' in results.headers)

        result = results.json[0]
        self.assertEqual(1, result['id'])
        result = results.json[1]
        self.assertEqual(2, result['id'])
        result = results.json[2]
        self.assertEqual(3, result['id'])
