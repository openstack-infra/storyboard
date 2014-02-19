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

AUTH_PREFIX = "/v1/openid"


class AuthTokenMiddleware(object):

    def __init__(self, app, allow_unauthorized=None):
        self.app = app
        self.allow_unauthorized = allow_unauthorized or []

    def _header_to_env_var(self, key):
        """Convert header to wsgi env variable.

        """
        return 'HTTP_%s' % key.replace('-', '_').upper()

    def _get_header(self, env, key, default=None):
        """Get http header from environment."""
        env_key = self._header_to_env_var(key)
        return env.get(env_key, default)

    def _get_url(self, env):
        return env.get("PATH_INFO")

    def _get_method(self, env):
        return env.get("REQUEST_METHOD")

    def _clear_params(self, url):
        return url.split("?")[0]

    def __call__(self, env, start_response):
        url = self._get_url(env)

        if url and url.startswith(AUTH_PREFIX):
            return self.app(env, start_response)

        return self.app(env, start_response)
