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

# Default allowed headers

ALLOWED_HEADERS = [
    'origin',
    'authorization',
    'accept'
]
# Default allowed methods
ALLOWED_METHODS = [
    'GET',
    'POST',
    'PUT',
    'DELETE',
    'OPTIONS'
]


class CORSMiddleware(object):
    """CORS Middleware.

    By providing a list of allowed origins, methods, headers, and a max-age,
    this middleware will detect and apply the appropriate CORS headers so
    that your web application may elegantly overcome the browser's
    same-origin sandbox.

    For more information, see http://www.w3.org/TR/cors/
    """

    def __init__(self, app, allowed_origins=None, allowed_methods=None,
                 allowed_headers=None, max_age=3600):
        """Create a new instance of the CORS middleware.

        :param app: The application that is being wrapped.
        :param allowed_origins: A list of allowed origins, as provided by the
        'Origin:' Http header. Must include protocol, host, and port.
        :param allowed_methods: A list of allowed HTTP methods.
        :param allowed_headers: A list of allowed HTTP headers.
        :param max_age: A maximum CORS cache age in seconds.
        :return: A new middleware instance.
        """

        # Wrapped app (or other middleware)
        self.app = app

        # Allowed origins
        self.allowed_origins = allowed_origins or []

        # List of allowed headers.
        self.allowed_headers = ','.join(allowed_headers or ALLOWED_HEADERS)

        # List of allowed methods.
        self.allowed_methods = ','.join(allowed_methods or ALLOWED_METHODS)

        # Cache age.
        self.max_age = str(max_age)

    def __call__(self, env, start_response):
        """Serve an application request.

        :param env: Application environment parameters.
        :param start_response: Wrapper method that starts the response.
        :return:
        """
        origin = env['HTTP_ORIGIN'] if 'HTTP_ORIGIN' in env else ''
        method = env['REQUEST_METHOD'] if 'REQUEST_METHOD' in env else ''

        def replacement_start_response(status, headers, exc_info=None):
            """Overrides the default response to attach CORS headers.
            """

            # Decorate the headers
            headers.append(('Access-Control-Allow-Origin',
                            origin))
            headers.append(('Access-Control-Allow-Methods',
                            self.allowed_methods))
            headers.append(('Access-Control-Expose-Headers',
                            self.allowed_headers))
            headers.append(('Access-Control-Allow-Headers',
                            self.allowed_headers))
            headers.append(('Access-Control-Max-Age',
                            self.max_age))

            return start_response(status, headers, exc_info)

        # Does this request match one of our origin domains?
        if origin in self.allowed_origins:

            # Is this an OPTIONS request?
            if method == 'OPTIONS':
                options_headers = [('Content-Length', '0')]
                replacement_start_response('204 No Content', options_headers)
                return ''
            else:
                # Handle the request.
                return self.app(env, replacement_start_response)
        else:
            # This is not a request for a permitted CORS domain. Return
            # the response without the appropriate headers and let the browser
            # figure out the details.
            return self.app(env, start_response)
