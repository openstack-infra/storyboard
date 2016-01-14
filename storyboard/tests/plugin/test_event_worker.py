# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing permissions and
# limitations under the License.

import storyboard.db.api.base as db_api_base
import storyboard.plugin.event_worker as plugin_base
import storyboard.tests.base as base


class TestWorkerTaskBase(base.FunctionalTest):
    def setUp(self):
        super(TestWorkerTaskBase, self).setUp()

    def test_resolve_by_name(self):
        '''Assert that resolve_resource_by_name works.'''

        worker = TestWorkerPlugin({})

        with base.HybridSessionManager():
            session = db_api_base.get_session()

            task = worker.resolve_resource_by_name(session, 'task', 1)
            self.assertIsNotNone(task)
            self.assertEqual(1, task.id)

            project_group = worker.resolve_resource_by_name(session,
                                                            'project_group', 1)
            self.assertIsNotNone(project_group)
            self.assertEqual(1, project_group.id)

            project = worker.resolve_resource_by_name(session, 'project', 1)
            self.assertIsNotNone(project)
            self.assertEqual(1, project.id)

            user = worker.resolve_resource_by_name(session, 'user', 1)
            self.assertIsNotNone(user)
            self.assertEqual(1, user.id)

            team = worker.resolve_resource_by_name(session, 'team', 1)
            self.assertIsNotNone(team)
            self.assertEqual(1, team.id)

            story = worker.resolve_resource_by_name(session, 'story', 1)
            self.assertIsNotNone(story)
            self.assertEqual(1, story.id)

            branch = worker.resolve_resource_by_name(session, 'branch', 1)
            self.assertIsNotNone(branch)
            self.assertEqual(1, branch.id)

            milestone = worker.resolve_resource_by_name(session,
                                                        'milestone', 1)
            self.assertIsNotNone(milestone)
            self.assertEqual(1, milestone.id)


class TestWorkerPlugin(plugin_base.WorkerTaskBase):
    def handle(self, session, author, method, url, path, query_string, status,
               resource, resource_id, sub_resource=None, sub_resource_id=None,
               resource_before=None, resource_after=None):
        pass

    def enabled(self):
        return True
