# Copyright (c) 2015 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from storyboard.db.api import base as db_base
from storyboard.tests import base
from storyboard.tests import mock_data


class BaseDbTestCase(base.DbTestCase):
    def setUp(self):
        super(BaseDbTestCase, self).setUp()

        self.original_get_session = db_base.get_session
        self.addCleanup(self._reset_get_session)
        db_base.get_session = self._mock_get_session

        mock_data.load()

    def _mock_get_session(self, autocommit=True, expire_on_commit=False,
                          in_request=True, **kwargs):
        return self.original_get_session(autocommit=autocommit,
                                         expire_on_commit=expire_on_commit,
                                         in_request=False, **kwargs)

    def _reset_get_session(self):
        db_base.get_session = self.original_get_session

    def _assert_saved_fields(self, expected, actual):
        for k in expected.keys():
            self.assertEqual(expected[k], actual[k])

    def _test_create(self, ref, save_method):
        saved = save_method(ref)

        self.assertIsNotNone(saved.id)
        self._assert_saved_fields(ref, saved)

    def _test_update(self, ref, delta, create, update):
        saved = create(ref)
        updated = update(saved.id, delta)

        self.assertEqual(saved.id, updated.id)
        self._assert_saved_fields(delta, updated)
