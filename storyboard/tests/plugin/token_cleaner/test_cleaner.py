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

from datetime import datetime
from datetime import timedelta

from oslo.config import cfg
import storyboard.db.api.base as db_api
from storyboard.db.models import AccessToken
from storyboard.plugin.token_cleaner.cleaner import TokenCleaner
import storyboard.tests.base as base
from storyboard.tests.mock_data import load_data


CONF = cfg.CONF


class TestTokenCleaner(base.FunctionalTest):
    """Test cases for our OAuth Token cleaner plugin."""

    def setUp(self):
        super(TestTokenCleaner, self).setUp()

    def tearDown(self):
        super(TestTokenCleaner, self).tearDown()

    def test_enabled(self):
        """Assert that this plugin responds to the flag set in our
        oauth configuration block.
        """
        CONF.set_override('enable', False, 'plugin_token_cleaner')
        plugin = TokenCleaner(CONF)
        self.assertFalse(plugin.enabled())

        CONF.set_override('enable', True, 'plugin_token_cleaner')
        plugin = TokenCleaner(CONF)
        self.assertTrue(plugin.enabled())

        CONF.clear_override('enable', 'plugin_token_cleaner')

    def test_interval(self):
        """Assert that the cron manager runs every 5 minutes."""
        plugin = TokenCleaner(CONF)
        self.assertEqual("? * * * *", plugin.interval())

    def test_token_removal(self):
        """Assert that the plugin deletes tokens whose expiration date passed
        over a week ago.
        """

        # Start with a clean database.
        db_api.model_query(AccessToken).delete()
        self.assertEqual(0, db_api.model_query(AccessToken).count())

        # Build 100 tokens, each one day older than the other, with 24 hour
        # expiration dates. I subtract 5 seconds here because the time it
        # takes to execute the script may, or may not, result in an
        # 8-day-old-token to remain valid.
        for i in range(0, 100):
            created_at = datetime.utcnow() - timedelta(days=i)
            expires_in = (60 * 60 * 24) - 5  # Minus five seconds, see above.
            expires_at = created_at + timedelta(seconds=expires_in)

            load_data([
                AccessToken(
                    user_id=1,
                    created_at=created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    expires_in=expires_in,
                    expires_at=expires_at.strftime('%Y-%m-%d %H:%M:%S'),
                    access_token='test_token_%s' % (i,))
            ])

        # Make sure we have 100 tokens.
        self.assertEqual(100, db_api.model_query(AccessToken).count())

        # Run the plugin.
        plugin = TokenCleaner(CONF)
        plugin.execute()

        # Make sure we have 8 tokens left (since one plugin starts today).
        self.assertEqual(8, db_api.model_query(AccessToken).count())
