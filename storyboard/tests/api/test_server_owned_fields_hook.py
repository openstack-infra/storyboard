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

import json

from storyboard.tests import base


class TestServerOwnedFieldsHook(base.FunctionalTest):
    def setUp(self):
        super(TestServerOwnedFieldsHook, self).setUp()
        self.default_headers['Authorization'] = 'Bearer valid_superuser_token'

    def invalid_change_time(self, resource):
        put_entity = {
            'created_at': "2014-01-01T00:00:00",
            'updated_at': "2014-01-01T00:00:00"
        }

        response = self.put_json(resource, put_entity)
        entity = json.loads(response.body)

        self.assertNotEquals(entity['created_at'], put_entity['created_at'])
        self.assertNotEquals(entity['updated_at'], put_entity['updated_at'])

    def invalid_create_time(self, resource, entity):
        entity['created_at'] = "2014-01-01T00:00:00"
        entity['updated_at'] = "2014-01-01T00:00:00"

        response = self.post_json(resource, entity)
        created_entity = json.loads(response.body)

        self.assertNotEquals(entity['created_at'],
                             created_entity['created_at'])
        self.assertNotEquals(entity['updated_at'],
                             created_entity['updated_at'])

    def test_projects_create(self):
        resource = '/projects'
        project = {
            'name': 'test-time-hook-project'
        }
        self.invalid_create_time(resource, project)

    def test_project_groups_create(self):
        resource = '/project_groups'
        project_group = {
            'name': 'test-time-hook-project-group',
            'title': 'some title'
        }
        self.invalid_create_time(resource, project_group)

    def test_stories_create(self):
        resource = '/stories'
        story = {
            'title': 'test-time-hook-story'
        }
        self.invalid_create_time(resource, story)

    def test_projects_update(self):
        resource = '/projects/1'
        self.invalid_change_time(resource)

    def test_project_groups_update(self):
        resource = '/project_groups/1'
        self.invalid_change_time(resource)

    def test_tasks_update(self):
        resource = '/tasks/1'
        self.invalid_change_time(resource)

    def test_users_update(self):
        resource = '/users/1'
        self.invalid_change_time(resource)
