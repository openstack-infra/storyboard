# Copyright 2014 OpenStack Foundation
# Copyright 2014 Mirantis Inc
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""
Tests for database migrations. This test case reads the configuration
file test_migrations.conf for database connection settings
to use in the tests. For each connection found in the config file,
the test case runs a series of test cases to ensure that migrations work
properly.

There are also "opportunistic" tests for both mysql and postgresql in here,
which allows testing against mysql and pg) in a properly configured unit
test environment.

For the opportunistic testing you need to set up a db named 'openstack_citest'
with user 'openstack_citest' and password 'openstack_citest' on localhost.
The test will then use that db and u/p combo to run the tests.

For postgres on Ubuntu this can be done with the following commands:

sudo -u postgres psql
postgres=# create user openstack_citest with createdb login password
      'openstack_citest';
postgres=# create database openstack_citest with owner openstack_citest;

"""

from oslo_config import cfg
from oslo_db.sqlalchemy import utils as db_utils

from storyboard.tests.db.migration import test_migrations_base as base

CONF = cfg.CONF


class TestMigrations(base.BaseWalkMigrationTestCase, base.CommonTestsMixIn):
    """Test sqlalchemy-migrate migrations."""
    USER = "openstack_citest"
    PASSWD = "openstack_citest"
    DATABASE = "openstack_citest"

    def __init__(self, *args, **kwargs):
        super(TestMigrations, self).__init__(*args, **kwargs)

    def setUp(self):
        super(TestMigrations, self).setUp()

    def assertColumnExists(self, engine, table, column):
        t = db_utils.get_table(engine, table)
        self.assertIn(column, t.c)

    def assertColumnNotExists(self, engine, table, column):
        t = db_utils.get_table(engine, table)
        self.assertNotIn(column, t.c)

    def assertIndexExists(self, engine, table, index):
        t = db_utils.get_table(engine, table)
        index_names = [idx.name for idx in t.indexes]
        self.assertIn(index, index_names)

    def assertIndexMembers(self, engine, table, index, members):
        self.assertIndexExists(engine, table, index)

        t = db_utils.get_table(engine, table)
        index_columns = None
        for idx in t.indexes:
            if idx.name == index:
                index_columns = idx.columns.keys()
                break

        self.assertEqual(sorted(members), sorted(index_columns))

    def _pre_upgrade_001(self, engine):
        # Anything returned from this method will be
        # passed to corresponding _check_xxx method as 'data'.
        pass

    def _check_001(self, engine, data):
        self.assertColumnExists(engine, 'users', 'created_at')
        self.assertColumnExists(engine, 'users', 'last_login')

        self.assertColumnExists(engine, 'teams', 'updated_at')
        self.assertColumnExists(engine, 'teams', 'name')

    def _check_002(self, engine, data):
        self.assertColumnExists(engine, 'users', 'openid')
        self.assertColumnNotExists(engine, 'users', 'password')

    def _check_003(self, engine, data):
        self.assertColumnExists(engine, 'projects', 'is_active')
        self.assertColumnExists(engine, 'stories', 'is_active')
        self.assertColumnExists(engine, 'tasks', 'is_active')

    def _check_004(self, engine, data):
        self.assertColumnExists(engine, 'projects', 'description')

    def _check_005(self, engine, data):
        self.assertColumnExists(engine, 'projects', 'is_active')
        self.assertColumnExists(engine, 'stories', 'is_active')
        self.assertColumnExists(engine, 'tasks', 'is_active')

    def _check_006(self, engine, data):
        self.assertColumnNotExists(engine, 'users', 'first_name')
        self.assertColumnNotExists(engine, 'users', 'last_name')
        self.assertColumnExists(engine, 'users', 'full_name')

    def _pre_upgrade_007(self, engine):
        self.assertColumnNotExists(engine, 'comments', 'is_active')

    def _check_007(self, engine, data):
        self.assertColumnExists(engine, 'comments', 'is_active')
