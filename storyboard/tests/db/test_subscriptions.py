# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
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

from storyboard.db.api.subscriptions import subscription_get_all_subscriber_ids
from storyboard.tests.db import base


class TestSubscription(base.BaseDbTestCase):
    '''Tests for the subscription db interface.
    '''

    def test_get_subscribers(self):
        '''Test subscription discovery. The tested algorithm is as follows:
        If you're subscribed to a project_group, you will be notified about
        project_group, project, story, and task changes. If you are
        subscribed to a project, you will be notified about project, story, and
        task changes. If you are subscribed to a task, you will be notified
        about changes to that task. If you are subscribed to a story,
        you will be notified about changes to that story and its tasks.

        '''

        subscribers = subscription_get_all_subscriber_ids('invalid', 1)
        self.assertSetEqual(set(), subscribers)

        subscribers = subscription_get_all_subscriber_ids('timeline_event', 1)
        self.assertSetEqual({1, 3}, subscribers)

        subscribers = subscription_get_all_subscriber_ids('story', 1)
        self.assertSetEqual({1, 3}, subscribers)
        subscribers = subscription_get_all_subscriber_ids('story', 2)
        self.assertSetEqual(set(), subscribers)
        subscribers = subscription_get_all_subscriber_ids('story', 3)
        self.assertSetEqual(set(), subscribers)
        subscribers = subscription_get_all_subscriber_ids('story', 4)
        self.assertSetEqual(set(), subscribers)
        subscribers = subscription_get_all_subscriber_ids('story', 5)
        self.assertSetEqual(set(), subscribers)

        subscribers = subscription_get_all_subscriber_ids('task', 1)
        self.assertSetEqual({1, 3}, subscribers)
        subscribers = subscription_get_all_subscriber_ids('task', 2)
        self.assertSetEqual({3}, subscribers)
        subscribers = subscription_get_all_subscriber_ids('task', 3)
        self.assertSetEqual({1, 3}, subscribers)
        subscribers = subscription_get_all_subscriber_ids('task', 4)
        self.assertSetEqual(set(), subscribers)

        subscribers = subscription_get_all_subscriber_ids('project', 1)
        self.assertSetEqual({1}, subscribers)
        subscribers = subscription_get_all_subscriber_ids('project', 2)
        self.assertSetEqual(set(), subscribers)
        subscribers = subscription_get_all_subscriber_ids('project', 3)
        self.assertSetEqual({1}, subscribers)

        subscribers = subscription_get_all_subscriber_ids('project_group', 1)
        self.assertSetEqual({1}, subscribers)
        subscribers = subscription_get_all_subscriber_ids('project_group', 2)
        self.assertSetEqual(set(), subscribers)
        subscribers = subscription_get_all_subscriber_ids('project_group', 3)
        self.assertSetEqual(set(), subscribers)
