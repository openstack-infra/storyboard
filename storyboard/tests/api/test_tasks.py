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

import six.moves.urllib.parse as urlparse

from storyboard.tests import base


class TestTasksPrimary(base.FunctionalTest):
    def setUp(self):
        super(TestTasksPrimary, self).setUp()
        self.resource = '/tasks'

        self.task_01 = {
            'title': 'StoryBoard',
            'status': 'todo',
            'story_id': 1
        }
        self.default_headers['Authorization'] = 'Bearer valid_superuser_token'

    def test_tasks_endpoint(self):
        response = self.get_json(self.resource)
        self.assertEqual(4, len(response))

    def test_create(self):
        result = self.post_json(self.resource, {
            'title': 'StoryBoard',
            'status': 'todo',
            'story_id': 1
        })

        # Retrieve the created task
        created_task = self \
            .get_json('%s/%d' % (self.resource, result.json['id']))
        self.assertEqual(result.json['id'], created_task['id'])
        self.assertEqual('StoryBoard', created_task['title'])
        self.assertEqual('todo', created_task['status'])
        self.assertEqual(1, created_task['story_id'])


class TestTasksNestedController(base.FunctionalTest):
    def setUp(self):
        super(TestTasksNestedController, self).setUp()
        self.resource = '/stories/1/tasks'

        self.task_01 = {
            'title': 'StoryBoard',
            'status': 'todo',
            'story_id': 1
        }
        self.default_headers['Authorization'] = 'Bearer valid_superuser_token'

    def test_tasks_endpoint(self):
        response = self.get_json(self.resource)
        self.assertEqual(3, len(response))

    def test_get(self):
        response = self.get_json(self.resource + "/1")
        # Get an existing task under a given story

        self.assertIsNotNone(response)

    def test_get_for_wrong_story(self):
        response = self.get_json(self.resource + "/4", expect_errors=True)
        # Get an existing task under a given story

        self.assertEqual(400, response.status_code)

    def test_create(self):
        result = self.post_json(self.resource, {
            'title': 'StoryBoard',
            'status': 'todo',
            'story_id': 1
        })

        # Retrieve the created task
        created_task = self \
            .get_json('%s/%d' % ("/tasks", result.json['id']))
        self.assertEqual(result.json['id'], created_task['id'])
        self.assertEqual('StoryBoard', created_task['title'])
        self.assertEqual('todo', created_task['status'])
        self.assertEqual(1, created_task['story_id'])

    def test_create_id_in_url(self):
        result = self.post_json(self.resource, {
            'title': 'StoryBoard',
            'status': 'todo',
        })
        # story_id is not set in the body. URL should handle that

        # Retrieve the created task
        created_task = self \
            .get_json('%s/%d' % ("/tasks", result.json['id']))
        self.assertEqual(result.json['id'], created_task['id'])
        self.assertEqual('StoryBoard', created_task['title'])
        self.assertEqual('todo', created_task['status'])
        self.assertEqual(1, created_task['story_id'])

    def test_create_error(self):
        result = self.post_json(self.resource, {
            'title': 'StoryBoard',
            'status': 'todo',
            'story_id': 100500
        }, expect_errors=True)

        # task.story_id does not match the URL
        self.assertEqual(400, result.status_code)

    def test_update(self):
        original_task = self.get_json(self.resource)[0]
        original_id = original_task["id"]

        result = self.put_json(self.resource + "/%s" % original_id, {
            'title': 'task_updated',
        })

        self.assertEqual(200, result.status_code)

    def test_update_error(self):
        original_task = self.get_json(self.resource)[0]
        original_id = original_task["id"]

        result = self.put_json(self.resource + "/%s" % original_id, {
            'title': 'task_updated',
            'story_id': 100500
        }, expect_errors=True)

        self.assertEqual(400, result.status_code)

    def test_delete(self):
        result = self.delete(self.resource + "/1")
        self.assertEqual(204, result.status_code)

    def test_delete_for_wrong_story(self):
        result = self.delete(self.resource + "/4", expect_errors=True)
        self.assertEqual(400, result.status_code)


class TestTaskSearch(base.FunctionalTest):
    def setUp(self):
        super(TestTaskSearch, self).setUp()

    def build_search_url(self, params=None, raw=''):
        if params:
            raw = urlparse.urlencode(params)
        return '/tasks?%s' % raw

    def test_search(self):
        url = self.build_search_url({
        })

        results = self.get_json(url, expect_errors=True)
        self.assertEqual(4, len(results.json))
        self.assertEqual('4', results.headers['X-Total'])
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

    def test_search_by_story_id(self):
        url = self.build_search_url({
            'story_id': 1
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

    def test_search_by_assignee_id(self):
        url = self.build_search_url({
            'assignee_id': 2
        })

        results = self.get_json(url, expect_errors=True)
        self.assertEqual(1, len(results.json))
        self.assertEqual('1', results.headers['X-Total'])
        self.assertFalse('X-Marker' in results.headers)

        result = results.json[0]
        self.assertEqual(1, result['id'])

    def test_search_by_project_id(self):
        url = self.build_search_url({
            'project_id': 2
        })

        results = self.get_json(url, expect_errors=True)
        self.assertEqual(2, len(results.json))
        self.assertEqual('2', results.headers['X-Total'])
        self.assertFalse('X-Marker' in results.headers)

        result = results.json[0]
        self.assertEqual(2, result['id'])
        result = results.json[1]
        self.assertEqual(4, result['id'])

    def test_search_by_project_group_id(self):
        url = self.build_search_url({
            'project_group_id': 2
        })

        results = self.get_json(url, expect_errors=True)
        self.assertEqual(3, len(results.json))
        self.assertEqual('3', results.headers['X-Total'])
        self.assertFalse('X-Marker' in results.headers)

        result = results.json[0]
        self.assertEqual(2, result['id'])
        result = results.json[1]
        self.assertEqual(3, result['id'])
        result = results.json[2]
        self.assertEqual(4, result['id'])

    def test_search_by_status(self):
        url = self.build_search_url({
            'status': 'merged'
        })

        results = self.get_json(url, expect_errors=True)
        self.assertEqual(2, len(results.json))
        self.assertEqual('2', results.headers['X-Total'])
        self.assertFalse('X-Marker' in results.headers)

        result = results.json[0]
        self.assertEqual(2, result['id'])
        result = results.json[1]
        self.assertEqual(4, result['id'])

    def test_search_by_statuses(self):
        url = self.build_search_url(raw='status=invalid&status=merged')

        results = self.get_json(url, expect_errors=True)
        self.assertEqual(3, len(results.json))
        self.assertEqual('3', results.headers['X-Total'])
        self.assertFalse('X-Marker' in results.headers)

        result = results.json[0]
        self.assertEqual(2, result['id'])
        result = results.json[1]
        self.assertEqual(3, result['id'])
        result = results.json[2]
        self.assertEqual(4, result['id'])

    def test_search_by_priority(self):
        url = self.build_search_url({
            'priority': 'medium'
        })

        results = self.get_json(url, expect_errors=True)
        self.assertEqual(2, len(results.json))
        self.assertEqual('2', results.headers['X-Total'])
        self.assertFalse('X-Marker' in results.headers)

        result = results.json[0]
        self.assertEqual(1, result['id'])
        result = results.json[1]
        self.assertEqual(4, result['id'])

    def test_search_by_priorities(self):
        url = self.build_search_url(raw='priority=high&priority=low')

        results = self.get_json(url, expect_errors=True)
        self.assertEqual(2, len(results.json))
        self.assertEqual('2', results.headers['X-Total'])
        self.assertFalse('X-Marker' in results.headers)

        result = results.json[0]
        self.assertEqual(2, result['id'])
        result = results.json[1]
        self.assertEqual(3, result['id'])

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
        self.assertEqual(4, len(results.json))
        self.assertEqual('4', results.headers['X-Total'])
        self.assertFalse('X-Marker' in results.headers)

        result = results.json[0]
        self.assertEqual(1, result['id'])
        result = results.json[1]
        self.assertEqual(2, result['id'])
        result = results.json[2]
        self.assertEqual(3, result['id'])
        result = results.json[3]
        self.assertEqual(4, result['id'])

    def test_search_direction_desc(self):
        url = self.build_search_url({
            'sort_field': 'title',
            'sort_dir': 'desc'
        })

        results = self.get_json(url, expect_errors=True)
        self.assertEqual(4, len(results.json))
        self.assertEqual('4', results.headers['X-Total'])
        self.assertFalse('X-Marker' in results.headers)

        result = results.json[0]
        self.assertEqual(4, result['id'])
        result = results.json[1]
        self.assertEqual(3, result['id'])
        result = results.json[2]
        self.assertEqual(2, result['id'])
        result = results.json[3]
        self.assertEqual(1, result['id'])
