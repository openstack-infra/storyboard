# -*- coding: utf-8 -*-

# Copyright 2010-2011 OpenStack Foundation
# Copyright (c) 2013 Hewlett-Packard Development Company, L.P.
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

import os
import shutil
import stat
import uuid

from alembic import command
import fixtures
from oslo_concurrency.fixture import lockutils as lockutils_fixture
from oslo_config import cfg
from oslo_log import log as logging
import pecan
import pecan.testing
import six
import sqlalchemy
import testtools

import storyboard.common.working_dir as working_dir
from storyboard.db.api import base as db_api_base
from storyboard.db.migration.cli import get_alembic_config
import storyboard.tests.mock_data as mock_data


CONF = cfg.CONF
_TRUE_VALUES = ('true', '1', 'yes')

_DB_CACHE = None

logging.register_options(CONF)
logging.setup(CONF, 'storyboard')


class TestCase(testtools.TestCase):

    """Test case base class for all unit tests."""

    def setUp(self):
        """Run before each test method to initialize test environment."""

        super(TestCase, self).setUp()
        test_timeout = os.environ.get('OS_TEST_TIMEOUT', 0)
        try:
            test_timeout = int(test_timeout)
        except ValueError:
            # If timeout value is invalid do not set a timeout.
            test_timeout = 0
        if test_timeout > 0:
            self.useFixture(fixtures.Timeout(test_timeout, gentle=True))

        env_test_db = os.environ.get('STORYBOARD_TEST_DB')
        if env_test_db is not None:
            self.test_connection = env_test_db
        else:
            self.test_connection = ("mysql+pymysql://openstack_citest:"
                                    "openstack_citest@127.0.0.1:3306")

        self.useFixture(fixtures.NestedTempfile())
        self.useFixture(fixtures.TempHomeDir())
        self.useFixture(lockutils_fixture.ExternalLockFixture())

        self.addCleanup(CONF.reset)

        if os.environ.get('OS_STDOUT_CAPTURE') in _TRUE_VALUES:
            stdout = self.useFixture(fixtures.StringStream('stdout')).stream
            self.useFixture(fixtures.MonkeyPatch('sys.stdout', stdout))
        if os.environ.get('OS_STDERR_CAPTURE') in _TRUE_VALUES:
            stderr = self.useFixture(fixtures.StringStream('stderr')).stream
            self.useFixture(fixtures.MonkeyPatch('sys.stderr', stderr))

        self.log_fixture = self.useFixture(fixtures.FakeLogger())

    def config(self, **kw):
        """Override some configuration values.

        The keyword arguments are the names of configuration options to
        override and their values.

        If a group argument is supplied, the overrides are applied to
        the specified configuration option group.

        All overrides are automatically cleared at the end of the current
        test by the fixtures cleanup process.
        """
        group = kw.pop('group', None)
        for k, v in six.iteritems(kw):
            CONF.set_override(k, v, group)


class WorkingDirTestCase(TestCase):
    """A test case that ensures that the configured working directory,
    if ever invoked, does not pollute the global working-directory space.
    """
    def setUp(self):
        super(WorkingDirTestCase, self).setUp()

        # First register the teardown.
        self.addCleanup(self._delete_working_dir)

        workdir = fixtures.TempDir()
        self.useFixture(workdir)
        temp_path = workdir.path
        CONF.set_override('working_directory', temp_path)

        # Create the directory
        path = working_dir.get_working_directory()
        self.assertTrue(os.path.exists(path))

    def _delete_working_dir(self):
        path = working_dir.get_working_directory()
        perms = stat.S_IRWXU + stat.S_IRWXG + stat.S_IRWXO

        if os.path.exists(path):
            os.chmod(path, perms)
            shutil.rmtree(path)

        self.assertFalse(os.path.exists(path))

        working_dir.WORKING_DIRECTORY = None


class DbTestCase(WorkingDirTestCase):

    def setUp(self):
        super(DbTestCase, self).setUp()
        self.setup_db()

    def setup_db(self):
        self.db_name = "storyboard_test_db_%s" % uuid.uuid4()
        self.db_name = self.db_name.replace("-", "_")

        # The engine w/o db name
        engine = sqlalchemy.create_engine(
            self.test_connection)
        engine.execute("CREATE DATABASE %s" % self.db_name)

        alembic_config = get_alembic_config()
        alembic_config.storyboard_config = CONF
        CONF.set_override(
            "connection",
            self.test_connection + "/%s"
            % self.db_name,
            group="database")

        command.upgrade(alembic_config, "head")
        self.addCleanup(self._drop_db)

    def _drop_db(self):
        engine = sqlalchemy.create_engine(
            self.test_connection)
        engine.execute("DROP DATABASE %s" % self.db_name)
        db_api_base.cleanup()

PATH_PREFIX = '/v1'


class HybridSessionManager(object):

    def _mock_get_session(self, autocommit=True, expire_on_commit=False,
                          in_request=True, **kwargs):
        return self.original_get_session(autocommit=autocommit,
                                         expire_on_commit=expire_on_commit,
                                         in_request=False, **kwargs)

    def __enter__(self):
        self.original_get_session = db_api_base.get_session
        db_api_base.get_session = self._mock_get_session

    def __exit__(self, exc_type, exc_val, exc_tb):
        db_api_base.get_session = self.original_get_session


class FunctionalTest(DbTestCase):
    """Used for functional tests of Pecan controllers where you need to
    test your literal application and its integration with the
    framework.
    """

    def setUp(self):
        super(FunctionalTest, self).setUp()

        self.default_headers = {}
        self.app = self._make_app()
        self.addCleanup(self._reset_pecan)
        self.addCleanup(self._clear_headers)
        mock_data.load()

    def _make_app(self):
        config = {
            'app': {
                'root': 'storyboard.api.root_controller.RootController',
                'modules': ['storyboard.api']
            }
        }
        return pecan.testing.load_test_app(config=config)

    def _reset_pecan(self):
        pecan.set_config({}, overwrite=True)

    def _clear_headers(self):
        self.default_headers = {}

    def _request_json(self, path, params, expect_errors=False, headers=None,
                      method="post", extra_environ=None, status=None,
                      path_prefix=PATH_PREFIX):
        """Sends simulated HTTP request to Pecan test app.

        :param path: url path of target service
        :param params: content for wsgi.input of request
        :param expect_errors: Boolean value; whether an error is expected based
                              on request
        :param headers: a dictionary of headers to send along with the request
        :param method: Request method type. Appropriate method function call
                       should be used rather than passing attribute in.
        :param extra_environ: a dictionary of environ variables to send along
                              with the request
        :param status: expected status code of response
        :param path_prefix: prefix of the url path
        """

        merged_headers = self.default_headers.copy()
        if headers:
            merged_headers.update(headers)

        full_path = path_prefix + path
        response = getattr(self.app, "%s_json" % method)(
            six.text_type(full_path),
            params=params,
            headers=merged_headers,
            status=status,
            extra_environ=extra_environ,
            expect_errors=expect_errors
        )
        return response

    def put_json(self, path, params, expect_errors=False, headers=None,
                 extra_environ=None, status=None):
        """Sends simulated HTTP PUT request to Pecan test app.

        :param path: url path of target service
        :param params: content for wsgi.input of request
        :param expect_errors: Boolean value; whether an error is expected based
                              on request
        :param headers: a dictionary of headers to send along with the request
        :param extra_environ: a dictionary of environ variables to send along
                              with the request
        :param status: expected status code of response
        """
        return self._request_json(path=path, params=params,
                                  expect_errors=expect_errors,
                                  headers=headers, extra_environ=extra_environ,
                                  status=status, method="put")

    def post_json(self, path, params, expect_errors=False, headers=None,
                  extra_environ=None, status=None):
        """Sends simulated HTTP POST request to Pecan test app.

        :param path: url path of target service
        :param params: content for wsgi.input of request
        :param expect_errors: Boolean value; whether an error is expected based
                              on request
        :param headers: a dictionary of headers to send along with the request
        :param extra_environ: a dictionary of environ variables to send along
                              with the request
        :param status: expected status code of response
        """
        return self._request_json(path=path, params=params,
                                  expect_errors=expect_errors,
                                  headers=headers, extra_environ=extra_environ,
                                  status=status, method="post")

    def patch_json(self, path, params, expect_errors=False, headers=None,
                   extra_environ=None, status=None):
        """Sends simulated HTTP PATCH request to Pecan test app.

        :param path: url path of target service
        :param params: content for wsgi.input of request
        :param expect_errors: Boolean value; whether an error is expected based
                              on request
        :param headers: a dictionary of headers to send along with the request
        :param extra_environ: a dictionary of environ variables to send along
                              with the request
        :param status: expected status code of response
        """
        return self._request_json(path=path, params=params,
                                  expect_errors=expect_errors,
                                  headers=headers, extra_environ=extra_environ,
                                  status=status, method="patch")

    def delete(self, path, expect_errors=False, headers=None,
               extra_environ=None, status=None, path_prefix=PATH_PREFIX):
        """Sends simulated HTTP DELETE request to Pecan test app.

        :param path: url path of target service
        :param expect_errors: Boolean value; whether an error is expected based
                              on request
        :param headers: a dictionary of headers to send along with the request
        :param extra_environ: a dictionary of environ variables to send along
                              with the request
        :param status: expected status code of response
        :param path_prefix: prefix of the url path
        """
        merged_headers = self.default_headers.copy()
        if headers:
            merged_headers.update(headers)

        full_path = path_prefix + path
        response = self.app.delete(six.text_type(full_path),
                                   headers=merged_headers,
                                   status=status,
                                   extra_environ=extra_environ,
                                   expect_errors=expect_errors)
        return response

    def get_json(self, path, expect_errors=False, headers=None,
                 extra_environ=None, q=[], path_prefix=PATH_PREFIX, **params):
        """Sends simulated HTTP GET request to Pecan test app.

        :param path: url path of target service
        :param expect_errors: Boolean value;whether an error is expected based
                              on request
        :param headers: a dictionary of headers to send along with the request
        :param extra_environ: a dictionary of environ variables to send along
                              with the request
        :param q: list of queries consisting of: field, value, op, and type
                  keys
        :param path_prefix: prefix of the url path
        :param params: content for wsgi.input of request
        """
        merged_headers = self.default_headers.copy()
        if headers:
            merged_headers.update(headers)

        full_path = path_prefix + path
        query_params = {'q.field': [],
                        'q.value': [],
                        'q.op': [],
                        }
        for query in q:
            for name in ['field', 'op', 'value']:
                query_params['q.%s' % name].append(query.get(name, ''))
        all_params = {}
        all_params.update(params)
        if q:
            all_params.update(query_params)
        response = self.app.get(full_path,
                                params=all_params,
                                headers=merged_headers,
                                extra_environ=extra_environ,
                                expect_errors=expect_errors)
        if not expect_errors:
            response = response.json
        return response

    def validate_link(self, link):
        """Checks if the given link can get correct data."""

        # removes 'http://loicalhost' part
        full_path = link.split('localhost', 1)[1]
        try:
            self.get_json(full_path, path_prefix='')
            return True
        except Exception:
            return False
