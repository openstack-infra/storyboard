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

from storyboard.api.v1.v1_controller import V1Controller
import storyboard.common.hook_priorities as priority
from storyboard.notifications.notification_hook import NotificationHook
import storyboard.tests.base as base


class TestNotificationHook(base.TestCase):

    def test_priority(self):
        """Assert that this hook has default priority."""
        self.assertEqual(NotificationHook.priority, priority.DEFAULT)

    def test_parse(self):
        """Test various permutations of the notification parser."""

        notifier = NotificationHook()

        self.assertEqual(
            ('project_group', '1', None, None),
            notifier.parse('/v1/project_groups/1')
        )
        self.assertEqual(
            ('project_group', '2', None, None),
            notifier.parse('/v1/project_groups/2')
        )
        self.assertEqual(
            ('project_group', '2', 'project', '1'),
            notifier.parse('/v1/project_groups/2/projects/1')
        )

        self.assertEqual(
            ('project', '2', None, None),
            notifier.parse('/v1/projects/2')
        )

        self.assertEqual(
            ('story', '2', None, None),
            notifier.parse('/v1/stories/2')
        )
        self.assertEqual(
            ('story', '2', 'comment', None),
            notifier.parse('/v1/stories/2/comments')
        )
        self.assertEqual(
            ('story', '2', 'comment', '4'),
            notifier.parse('/v1/stories/2/comments/4')
        )
        self.assertEqual(
            ('task', '2', None, None),
            notifier.parse('/v1/tasks/2')
        )
        self.assertEqual(
            (None, None, None, None),
            notifier.parse('/v1/openid/authorize')
        )

    def test_singularize_resource(self):
        """Enforce singularization for all first level resources. This acts
        as a catchall to make sure that newly added resources are registered
        in the singularization method.
        """
        n = NotificationHook()

        # Extract all resource names from the root level resource.
        keys = vars(V1Controller).keys()
        for key in keys:
            # Strip out private things.
            if key[0:2] == '__':
                continue

            singular = n.singularize_resource(key)
            self.assertIsNotNone(singular)

        # Special case some second-level cases that matter:
        self.assertEqual('comment',
                         n.singularize_resource('comments'))

        # Confirm that the expected values are returned.
        self.assertEqual('story',
                         n.singularize_resource('stories'))
        self.assertEqual('project',
                         n.singularize_resource('projects'))
        self.assertEqual('project_group',
                         n.singularize_resource('project_groups'))
        self.assertEqual('timeline_event',
                         n.singularize_resource('timeline_events'))
        self.assertEqual('user',
                         n.singularize_resource('users'))
        self.assertEqual('team',
                         n.singularize_resource('teams'))
        self.assertEqual('tag',
                         n.singularize_resource('tags'))
        self.assertEqual('task_status',
                         n.singularize_resource('task_statuses'))
        self.assertEqual('subscription',
                         n.singularize_resource('subscriptions'))
        self.assertEqual('subscription_event',
                         n.singularize_resource('subscription_events'))
        self.assertEqual('systeminfo',
                         n.singularize_resource('systeminfo'))
        self.assertEqual('openid',
                         n.singularize_resource('openid'))
