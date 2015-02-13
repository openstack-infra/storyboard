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
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re

from webob.acceptparse import Accept


class BrowserRedirectMiddleware(object):
    # A list of HTML Headers that may come from browsers.
    html_headers = [
        'text/html',
        'application/xhtml+xml'
    ]

    def __init__(self, app, client_root_url='/'):
        """Build an HTTP redirector, with the initial assumption that the
        client is installed on the same host as this wsgi app.

        :param app The WSGI app to wrap.
        :param client_root_url The root URL of the redirect target's path.
        """
        self.app = app
        self.client_root_url = client_root_url

    def __call__(self, env, start_response):
        # We only care about GET methods.
        if env['REQUEST_METHOD'] == 'GET' and 'HTTP_ACCEPT' in env:
            # Iterate over the headers.
            for type, quality in Accept.parse(env['HTTP_ACCEPT']):
                # Only accept quality 1 headers, anything less
                # implies that the client prefers something else.
                if quality == 1 and type in self.html_headers:
                    # Build the redirect URL and redirect if successful
                    redirect_to = self._build_redirect_url(env['PATH_INFO'])
                    if redirect_to:
                        start_response("303 See Other",
                                       [('Location', redirect_to)])
                        return []

                    # Otherwise, break out of the whole loop and let the
                    # default handler deal with it.
                    break

        return self.app(env, start_response)

    def _build_redirect_url(self, path):
        # To map to the client, we are assuming that the API adheres to a URL
        # pattern of "/superfluous_prefix/v1/other_things. We strip out
        # anything up to and including /v1, and use the rest as our redirect
        # fragment. Note that this middleware makes no assumption about #!
        # navigation, as it is feasible that true HTML5 history support is
        # available on the client.
        match = re.search('\/v1(\/.*$)', path)
        if match:
            return self.client_root_url + match.group(1)
        else:
            return None
