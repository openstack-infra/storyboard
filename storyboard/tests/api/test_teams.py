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

from storyboard.tests import base


class TestTeams(base.FunctionalTest):
    def setUp(self):
        super(TestTeams, self).setUp()
        self.resource = '/teams'
        self.default_headers['Authorization'] = 'Bearer valid_superuser_token'

    def test_delete_invalid(self):
        # create new empty team with name 'testTeam'
        response = self.post_json(self.resource, {'name': 'testTeam'})
        body = response.json
        self.assertEqual('testTeam', body['name'])

        # add user with id = 2 to team with name 'testTeam'
        resource = (self.resource + '/%d') % body['id']
        response = self.put_json(resource + '/users', {'user_id': '2'})
        self.assertEqual(200, response.status_code)

        # try to delete team with name 'testTeam'
        # team with name 'testTeam' can't be deleted, because she isn't empty
        # only empty teams can be deleted
        response = self.delete(resource, expect_errors=True)
        self.assertEqual(400, response.status_code)

    def test_delete(self):
        # create new team with name 'testTeam'
        response = self.post_json(self.resource, {'name': 'testTeam'})
        body = response.json
        self.assertEqual('testTeam', body['name'])
        resource = (self.resource + '/%d') % body['id']

        # delete team with name 'testTeam'
        # team with name 'testTeam' can be deleted, because she is empty
        # only empty teams can be deleted
        response = self.delete(resource)
        self.assertEqual(204, response.status_code)

        # check that team with name 'testTeam' doesn't exist now
        response = self.get_json(resource, expect_errors=True)
        self.assertEqual(404, response.status_code)
