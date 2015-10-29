# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
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

import copy
import mock
import six
import smtplib

from oslo_config import cfg

import storyboard.db.api.base as db_api_base
import storyboard.db.models as models
from storyboard.plugin.email.workers import EmailWorkerBase
from storyboard.plugin.email.workers import SubscriptionEmailWorker
from storyboard.tests import base


CONF = cfg.CONF


class TestEmailWorkerBase(base.FunctionalTest):

    def test_handle(self):
        """Assert that the handle method passes the correct values on."""
        worker_base = MockEmailWorkerBase({})

        with base.HybridSessionManager():
            session = db_api_base.get_session()
            user_1 = db_api_base.entity_get(models.User, 1, session=session)

            worker_base.handle(session=session,
                               author=user_1,
                               method='POST',
                               path='/test',
                               status=201,
                               resource='story',
                               resource_id=1)

            self.assertIsInstance(worker_base.handled_values['author'],
                                  models.User)
            self.assertEqual(1, worker_base.handled_values['author'].id)

            self.assertEqual(2, len(worker_base.handled_values['subscribers']))
            self.assertEqual('POST', worker_base.handled_values['method'])
            self.assertEqual(201, worker_base.handled_values['status'])
            self.assertEqual('/test', worker_base.handled_values['path'])
            self.assertEqual('story', worker_base.handled_values['resource'])
            self.assertEqual(1, worker_base.handled_values['resource_id'])

    def test_get_subscribers(self):
        """Assert that the get_subscribers method functions as expected."""
        worker_base = MockEmailWorkerBase({})

        with base.HybridSessionManager():
            session = db_api_base.get_session()

            # Users 1 and 3 are subscribed to this story, user 1 as digest
            # and user 3 as individual emails.
            subscribers = worker_base.get_subscribers(session, 'story', 1)
            self.assertEqual(2, len(subscribers))
            self.assertEqual(1, subscribers[0].id)
            self.assertEqual(3, subscribers[1].id)

    def test_get_preference(self):
        """Assert that the get_preference method functions as expected."""
        worker_base = MockEmailWorkerBase({})

        with base.HybridSessionManager():
            session = db_api_base.get_session()
            user_1 = db_api_base.entity_get(models.User, 1, session=session)

            foo_value = worker_base.get_preference('foo', user_1)
            self.assertEqual('bar', foo_value)

            no_value = worker_base.get_preference('no_value', user_1)
            self.assertIsNone(no_value)

    def test_get_changed_properties(self):
        """Assert that changed properties are correctly detected."""
        worker_base = MockEmailWorkerBase({})

        # Null checks
        before, after = worker_base.get_changed_properties(None, {})
        self.assertIsNone(before)
        self.assertIsNone(after)
        before, after = worker_base.get_changed_properties(None, None)
        self.assertIsNone(before)
        self.assertIsNone(after)
        before, after = worker_base.get_changed_properties({}, None)
        self.assertIsNone(before)
        self.assertIsNone(after)

        # Comparison check
        before, after = worker_base.get_changed_properties({
            'foo': 'bar',
            'lol': 'cats',
            'created_at': 'some_date',
            'before_only': 'value'
        }, {
            'foo': 'bar',
            'lol': 'dogs',
            'created_at': 'some_other_date',
            'after_only': 'value'
        })
        self.assertIsNotNone(before)
        self.assertIsNotNone(after)
        self.assertEqual(3, len(before.keys()))
        self.assertIn('before_only', before.keys())
        self.assertIn('after_only', before.keys())
        self.assertIn('lol', before.keys())
        self.assertIn('before_only', after.keys())
        self.assertIn('after_only', after.keys())
        self.assertIn('lol', after.keys())

        self.assertEqual('cats', before['lol'])
        self.assertEqual('dogs', after['lol'])
        self.assertEqual('value', after['after_only'])
        self.assertEqual(None, before['after_only'])
        self.assertEqual('value', before['before_only'])
        self.assertEqual(None, after['before_only'])


class TestSubscriptionEmailWorker(base.FunctionalTest):
    @mock.patch('storyboard.plugin.email.smtp_client.get_smtp_client')
    def test_handle_email(self, get_smtp_client):
        """Make sure that events from the queue are sent as emails."""
        dummy_smtp = mock.Mock(smtplib.SMTP)
        worker_base = SubscriptionEmailWorker({})
        get_smtp_client.return_value.__enter__ = dummy_smtp

        with base.HybridSessionManager():
            session = db_api_base.get_session()
            author = db_api_base.entity_get(models.User, 2, session=session)
            story = db_api_base.entity_get(models.Story, 1, session=session)
            story_dict = story.as_dict()
            story_after_dict = copy.copy(story_dict)
            story_after_dict['title'] = 'New Test Title'

            subscribers = worker_base.get_subscribers(session, 'story', 1)
            self.assertEqual(2, len(subscribers))

            worker_base.handle_email(session=session,
                                     author=author,
                                     subscribers=subscribers,
                                     method='PUT',
                                     path='/stories/1',
                                     status=200,
                                     resource='story',
                                     resource_id=1,
                                     resource_before=story_dict,
                                     resource_after=story_after_dict)
            # There should be two subscribers, but only one should get an
            # email since the other is a digest receiver.

            subscribed_user = db_api_base.entity_get(models.User, 3,
                                                     session=session)
            self.assertEqual(dummy_smtp.return_value.sendmail.call_count, 1)
            self.assertEqual(
                dummy_smtp.return_value.sendmail.call_args[1]['to_addrs'],
                subscribed_user.email)

    def test_get_templates(self):
        """Make sure the get_templates method behaves as expected."""
        worker_base = SubscriptionEmailWorker({})

        # Basic template test.
        subject, txt, html = worker_base.get_templates(method='POST',
                                                       resource_name='story',
                                                       sub_resource_name=None)
        self.assertEqual('story/POST_subject.txt', subject)
        self.assertEqual('story/POST.txt', txt)
        self.assertEqual('story/POST.html', html)

        # Subresource template test.
        subject, txt, html = worker_base.get_templates(method='POST',
                                                       resource_name='story',
                                                       sub_resource_name='f')
        self.assertEqual('story/f/POST_subject.txt', subject)
        self.assertEqual('story/f/POST.txt', txt)
        self.assertEqual('story/f/POST.html', html)


class MockEmailWorkerBase(EmailWorkerBase):
    """Mock instantiation of the abstract base class."""

    def handle_email(self, **kwargs):
        self.handled_values = {}

        for key, value in six.iteritems(kwargs):
            self.handled_values[key] = value
