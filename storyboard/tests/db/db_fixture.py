# Copyright (c) 2014 Mirantis Inc.
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
import eventlet
eventlet.monkey_patch(os=False)


import os
import warnings

from alembic import context, script, environment
from alembic import config as alembic_config
import fixtures
from oslo.config import cfg
from sqlalchemy.exc import SADeprecationWarning
from storyboard.openstack.common.db.sqlalchemy import session

CONF = cfg.CONF

warnings.simplefilter("ignore", SADeprecationWarning)


class Database(fixtures.Fixture):

    def __init__(self):
        config = alembic_config.Config(os.path.join(
            os.path.dirname(__file__),
            "../../db/migration/alembic.ini"))
        config.set_main_option(
            'script_location',
            'storyboard.db.migration:alembic_migrations')
        config.storyboard_config = CONF

        self.engine = session.get_engine()
        conn = self.engine.connect()
        self._sync_db(config, conn)

        self._DB = "".join(line for line in conn.connection.iterdump())
        self.engine.dispose()

    def _sync_db(self, config, conn):
        _script = script.ScriptDirectory.from_config(config)

        def upgrade(rev, context):
            return _script._upgrade_revs('head', rev)

        with environment.EnvironmentContext(
            config,
            _script,
            fn=upgrade,
        ):
            context.configure(connection=conn)
            with context.begin_transaction():
                context.run_migrations()

    def setUp(self):
        super(Database, self).setUp()

        conn = self.engine.connect()
        conn.connection.executescript(self._DB)
        self.addCleanup(self.engine.dispose)
