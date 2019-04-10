# Copyright (c) 2013 Mirantis Inc.
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

import unittest

import six.moves.urllib.parse as urlparse

from storyboard.db.api import tasks
from storyboard.tests import base


class TestStories(base.FunctionalTest):
    def setUp(self):
        super(TestStories, self).setUp()
        self.resource = '/stories'

        self.story_01 = {
            'title': 'StoryBoard',
            'description': 'Awesome Task Tracker'
        }
        self.default_headers['Authorization'] = 'Bearer valid_superuser_token'

    def test_stories_endpoint(self):
        response = self.get_json(self.resource)
        self.assertEqual(6, len(response))

    def test_private_story_visibility(self):
        url = self.resource + '/6'
        story = self.get_json(url)

        # User with token `valid_superuser_token` has permission to see
        # the story, so should be able to get it without issue.
        self.assertEqual(story['title'], 'Test Private Story')
        self.assertTrue(story['private'])
        self.assertEqual(1, len(story['users']))
        self.assertEqual('Super User', story['users'][0]['full_name'])
        self.assertEqual(0, len(story['teams']))

        # User with token `valid_user_token` doesn't have permission
        headers = {'Authorization': 'Bearer valid_user_token'}
        response = self.get_json(url, headers=headers, expect_errors=True)
        self.assertEqual(404, response.status_code)

        # Unauthenticated users shouldn't be able to see private stories
        self.default_headers.pop('Authorization')
        response = self.get_json(url, expect_errors=True)
        self.assertEqual(404, response.status_code)

    def test_create(self):
        response = self.post_json(self.resource, self.story_01)
        story = response.json

        url = "%s/%d" % (self.resource, story['id'])
        story = self.get_json(url)

        self.assertIn('id', story)
        self.assertIn('created_at', story)
        self.assertEqual(story['title'], self.story_01['title'])
        self.assertEqual(story['description'], self.story_01['description'])
        self.assertEqual(1, story['story_type_id'])

    def test_create_feature(self):
        story = {
            'title': 'StoryBoard',
            'description': 'Awesome Task Tracker',
            'story_type_id': 2
        }
        response = self.post_json(self.resource, story)
        created_story = response.json

        self.assertEqual(story['title'], created_story['title'])
        self.assertEqual(story['description'], created_story['description'])
        self.assertEqual(story['story_type_id'],
                         created_story['story_type_id'])

    def test_create_private_story(self):
        story = {
            'title': 'StoryBoard',
            'description': 'Awesome Task Tracker',
            'private': True,
            'users': [{'id': 1}]
        }
        response = self.post_json(self.resource, story)
        created_story = response.json

        self.assertEqual(story['title'], created_story['title'])
        self.assertEqual(story['description'], created_story['description'])
        self.assertEqual(story['private'],
                         created_story['private'])

    @unittest.skip("public vulnerabilities are not supported.")
    def test_create_public_vulnerability(self):
        story = {
            'title': 'StoryBoard',
            'description': 'Awesome Task Tracker',
            'story_type_id': 4
        }
        response = self.post_json(self.resource, story,
                                  expect_errors=True)
        self.assertEqual(400, response.status_code)

    def test_update(self):
        response = self.post_json(self.resource, self.story_01)
        original = response.json

        delta = {
            'id': original['id'],
            'title': 'new title',
            'description': 'new description'
        }

        url = "/stories/%d" % original['id']
        response = self.put_json(url, delta)
        updated = response.json

        self.assertEqual(updated['id'], original['id'])

        self.assertNotEqual(updated['title'], original['title'])
        self.assertNotEqual(updated['description'],
                            original['description'])

    def test_update_story_types(self):
        story = {
            'title': 'StoryBoard',
            'description': 'Awesome Task Tracker',
            'story_type_id': 1
        }

        response = self.post_json(self.resource, story)
        created_story = response.json

        self.assertEqual(story['story_type_id'],
                         created_story['story_type_id'])

        story_types = [2, 1]

        for story_type_id in story_types:
            response = self.put_json(self.resource +
                                     ('/%s' % created_story["id"]),
                                     {'story_type_id': story_type_id})
            self.assertEqual(story_type_id, response.json['story_type_id'])

    def test_update_private_to_public(self):
        story = {
            'title': 'StoryBoard',
            'description': 'Awesome Task Tracker',
            'private': True
        }

        response = self.post_json(self.resource, story)
        created_story = response.json

        self.assertEqual(story['private'],
                         created_story['private'])

        response = self.put_json(self.resource +
                                 ('/%s' % created_story['id']),
                                 {'private': False})
        updated_story = response.json
        self.assertFalse(updated_story['private'])

        # Check that a different user can see the story
        headers = {'Authorization': 'Bearer valid_user_token'}
        api_story = self.get_json(self.resource + '/%s' % created_story['id'],
                                  headers=headers)
        self.assertEqual(story['title'], api_story['title'])
        self.assertEqual(story['description'], api_story['description'])

    def test_update_restricted_branches(self):
        response = self.put_json(self.resource + '/1', {'story_type_id': 2},
                                 expect_errors=True)
        self.assertEqual(400, response.status_code)

    def test_update_invalid(self):
        response = self.put_json(self.resource + '/1', {'story_type_id': 2},
                                 expect_errors=True)
        self.assertEqual(400, response.status_code)

    def test_add_tags(self):
        url = "/stories/%d/tags" % 1
        response = self.put_json(url, ["tag_1", "tag_2"])
        updated = response.json

        self.assertEqual(2, len(updated["tags"]))
        response = self.get_json('/stories/1/events')

        self.assertEqual(4, len(response))
        self.assertEqual('tags_added', response[3]['event_type'])

    def test_add_tags_duplicate_error(self):
        url = "/stories/%d/tags" % 1
        response = self.put_json(url, ["tag_1", "tag_2"])
        updated = response.json

        self.assertEqual(2, len(updated["tags"]))
        response = self.put_json(url, ["tag_1", "tag_2"], expect_errors=True)
        self.assertEqual(400, response.status_code)

    def test_remove_unassigned_tags_error(self):
        url = "/stories/%d/tags" % 1
        response = self.put_json(url, ["tag_1", "tag_2"])
        updated = response.json

        self.assertEqual(2, len(updated["tags"]))
        response = self.delete(url + "?tags=tag_4&tags=tag_5",
                               expect_errors=True)
        self.assertEqual(404, response.status_code)

    def test_remove_tags(self):
        url = "/stories/%d/tags" % 1
        response = self.put_json(url, ["tag_1", "tag_2"])
        updated = response.json

        self.assertEqual(2, len(updated["tags"]))

        self.delete(url + "?tags=tag_1")
        response = self.get_json(self.resource + "/1")

        self.assertEqual(1, len(response["tags"]))

        response = self.get_json('/stories/1/events')

        self.assertEqual(5, len(response))
        self.assertEqual('tags_deleted', response[4]['event_type'])


class TestStorySearch(base.FunctionalTest):
    def setUp(self):
        super(TestStorySearch, self).setUp()

        self.resource = '/stories'

    def build_search_url(self, params=None, raw=''):
        if params:
            raw = urlparse.urlencode(params)
        return '/stories?%s' % raw

    def test_search(self):
        url = self.build_search_url({
        })

        results = self.get_json(url, expect_errors=True)
        self.assertEqual(5, len(results.json))
        self.assertEqual('5', results.headers['X-Total'])
        self.assertFalse('X-Marker' in results.headers)

    def test_search_by_title(self):
        url = self.build_search_url({
            'title': 'foo'
        })

        results = self.get_json(url, expect_errors=True)
        self.assertEqual(2, len(results.json))
        self.assertEqual('2', results.headers['X-Total'])
        self.assertFalse('X-Marker' in results.headers)

        result = results.json[0]
        self.assertEqual(1, result['id'])
        result = results.json[1]
        self.assertEqual(3, result['id'])

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

    def test_search_by_status(self):
        url = self.build_search_url({
            'status': 'active'
        })

        results = self.get_json(url, expect_errors=True)
        self.assertEqual(1, len(results.json))
        self.assertEqual('1', results.headers['X-Total'])
        self.assertFalse('X-Marker' in results.headers)

        result = results.json[0]
        self.assertEqual(1, result['id'])

    def test_search_by_statuses(self):
        url = self.build_search_url(raw='status=active&status=merged')

        results = self.get_json(url, expect_errors=True)
        self.assertEqual(2, len(results.json))
        self.assertEqual('2', results.headers['X-Total'])
        self.assertFalse('X-Marker' in results.headers)

        result = results.json[0]
        self.assertEqual(1, result['id'])
        result = results.json[1]
        self.assertEqual(2, result['id'])

    def test_search_by_assignee_id(self):
        url = self.build_search_url({
            'assignee_id': 1
        })

        results = self.get_json(url, expect_errors=True)
        self.assertEqual(2, len(results.json))
        self.assertEqual('2', results.headers['X-Total'])
        self.assertFalse('X-Marker' in results.headers)

        result = results.json[0]
        self.assertEqual(1, result['id'])
        result = results.json[1]
        self.assertEqual(2, result['id'])

    def test_search_by_project_group_id(self):
        url = self.build_search_url({
            'project_group_id': 2
        })

        results = self.get_json(url, expect_errors=True)
        self.assertEqual(2, len(results.json))
        self.assertEqual('2', results.headers['X-Total'])
        self.assertFalse('X-Marker' in results.headers)

        result = results.json[0]
        self.assertEqual(1, result['id'])
        result = results.json[1]
        self.assertEqual(2, result['id'])

    def test_search_by_project_id(self):
        url = self.build_search_url({
            'project_id': 1
        })

        results = self.get_json(url, expect_errors=True)
        self.assertEqual(1, len(results.json))
        self.assertEqual('1', results.headers['X-Total'])
        self.assertFalse('X-Marker' in results.headers)

        result = results.json[0]
        self.assertEqual(1, result['id'])

    def test_get_by_tags(self):
        tag_url_template = "/stories/%d/tags"
        self.default_headers['Authorization'] = 'Bearer valid_user_token'

        story_1 = self.get_json(self.resource + "/1")
        self.put_json(tag_url_template % story_1["id"], ["tag_1", "tag_2"])

        story_2 = self.get_json(self.resource + "/2")
        self.put_json(tag_url_template % story_2["id"], ["tag_2", "tag_3"])

        # Get the first only
        tag_query_results = self.get_json(self.resource, tags=["tag_1"])
        self.assertEqual(1, len(tag_query_results))
        self.assertEqual(1, tag_query_results[0]["id"])

        # Get the second only
        tag_query_results = self.get_json(self.resource, tags=["tag_3"])
        self.assertEqual(1, len(tag_query_results))
        self.assertEqual(2, tag_query_results[0]["id"])

        # Get both
        tag_query_results = self.get_json(self.resource, tags=["tag_2"])
        self.assertEqual(2, len(tag_query_results))

        # Get stories, which have tag_1 or tag_3
        tag_query_results = self.get_json(self.resource,
                                          tags=["tag_1", "tag_3"],
                                          tags_filter_type="any")
        self.assertEqual(2, len(tag_query_results))
        self.assertEqual(1, tag_query_results[0]["id"])
        self.assertEqual(2, tag_query_results[1]["id"])

        # Get stories, which have tag_1 with tags filter type 'any'
        tag_query_results = self.get_json(self.resource,
                                          tags=["tag_1"],
                                          tags_filter_type="any")
        self.assertEqual(1, len(tag_query_results))
        self.assertEqual(1, tag_query_results[0]["id"])

    def test_search_empty_results(self):
        url = self.build_search_url({
            'title': 'grumpycat'
        })

        results = self.get_json(url, expect_errors=True)
        self.assertEqual(0, len(results.json))
        self.assertEqual('0', results.headers['X-Total'])
        self.assertFalse('X-Marker' in results.headers)

    def test_search_limit(self):
        url = self.build_search_url({
            'title': 'foo',
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
            'title': 'foo',
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
            'sort_field': 'title',
            'sort_dir': 'asc'
        })

        results = self.get_json(url, expect_errors=True)
        self.assertEqual(5, len(results.json))
        self.assertEqual('5', results.headers['X-Total'])
        self.assertFalse('X-Marker' in results.headers)

        result = results.json[0]
        self.assertEqual(5, result['id'])
        result = results.json[1]
        self.assertEqual(4, result['id'])
        result = results.json[2]
        self.assertEqual(3, result['id'])
        result = results.json[3]
        self.assertEqual(2, result['id'])
        result = results.json[4]
        self.assertEqual(1, result['id'])

    def test_search_direction_desc(self):
        url = self.build_search_url({
            'sort_field': 'title',
            'sort_dir': 'desc'
        })

        results = self.get_json(url, expect_errors=True)
        self.assertEqual(5, len(results.json))
        self.assertEqual('5', results.headers['X-Total'])
        self.assertFalse('X-Marker' in results.headers)

        result = results.json[0]
        self.assertEqual(1, result['id'])
        result = results.json[1]
        self.assertEqual(2, result['id'])
        result = results.json[2]
        self.assertEqual(3, result['id'])
        result = results.json[3]
        self.assertEqual(4, result['id'])
        result = results.json[4]
        self.assertEqual(5, result['id'])

    def test_filter_paged_status(self):
        url = self.build_search_url({
            'limit': '2',
            'sort_field': 'id',
            'status': 'invalid'
        })

        results = self.get_json(url)
        self.assertEqual(2, len(results))
        result = results[0]
        self.assertEqual(3, result['id'])
        result = results[1]
        self.assertEqual(4, result['id'])


class TestStoryStatuses(base.FunctionalTest):
    def setUp(self):
        super(TestStoryStatuses, self).setUp()
        self.resource = '/stories'
        self.individual_resource = '/stories/1'

        self.default_headers['Authorization'] = 'Bearer valid_superuser_token'
        self.task_statuses = tasks.task_get_statuses().keys()

    # check if all stories are returning all statuses
    def test_stories_statuses(self):
        response = self.get_json(self.resource)

        all_statuses = True
        for story in response:
            current_statuses = story.get('task_statuses', [])
            final_statuses = []
            for status in current_statuses:
                final_statuses.append(status['key'])
            if set(final_statuses) != set(self.task_statuses):
                all_statuses = False
                break
        self.assertTrue(all_statuses)

    # verify that the returned count is real
    def test_story_count(self):
        response = self.get_json(self.individual_resource)
        task_statuses = response.get('task_statuses', [])
        story_id = response.get('id', None)
        all_tasks = self.get_json("/tasks", story_id=story_id)

        # get count of all statuses
        statuses_count = {}
        for task in all_tasks:
            current_status = task["status"]
            status_count = statuses_count.get(current_status, 0)
            statuses_count[current_status] = status_count + 1

        count_matches = True
        for status in task_statuses:
            status_count = statuses_count.get(status['key'], 0)
            if status_count != status['count']:
                count_matches = False
                break
        self.assertTrue(count_matches)
