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


class TestTags(base.FunctionalTest):
    def setUp(self):
        super(TestTags, self).setUp()
        self.resource = '/tags'

        self.tag_01 = {
            'name': 'TestTag',
        }
        self.default_headers['Authorization'] = 'Bearer valid_user_token'

    def test_tags_endpoint(self):
        response = self.get_json(self.resource)
        self.assertEqual(0, len(response))

    def test_create(self):
        response = self.post_json(self.resource, params={
            "tag_name": self.tag_01["name"]})
        tag = response.json

        url = "%s/%d" % (self.resource, tag['id'])
        tag = self.get_json(url)

        self.assertIn('id', tag)
        self.assertIn('created_at', tag)
        self.assertEqual(tag['name'], self.tag_01['name'])
