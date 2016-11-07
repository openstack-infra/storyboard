# Copyright (c) 2015 Mirantis Inc.
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

import functools
from pecan import abort
from pecan import redirect
from pecan import response
from six.moves.urllib.parse import urlencode
from six.moves.urllib.parse import urlparse
from six.moves.urllib.parse import urlunparse

from storyboard._i18n import _
from storyboard.common import exception as exc


def db_exceptions(func):
    @functools.wraps(func)
    def decorate(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except exc.DBException as db_exc:
            abort(db_exc.code, db_exc.message)

    return decorate


def oauth_exceptions(func):
    @functools.wraps(func)
    def decorate(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except exc.OAuthException as o_exc:

            # Extract the parameters
            error = o_exc.error
            error_description = o_exc.msg or _("No details available.")

            # If we have a redirect URL, build the error redirect.
            if o_exc.redirect_uri:
                # Split the redirect_url apart
                parts = urlparse(o_exc.redirect_uri)

                # Add the error and error_description
                if parts.query:
                    params = urlparse.parse_qsl(parts.query)
                else:
                    params = []
                params.append(('error', error))
                params.append(('error_description', error_description))

                # Overwrite the old query params and reconstruct the URL
                parts_list = list(parts)
                parts_list[4] = urlencode(params)
                location = urlunparse(parts_list)

                redirect(location)
            else:
                error_body = {
                    'error': error,
                    'error_description': error_description
                }
                response.json = error_body
                abort(o_exc.code, error_description, json_body=error_body)

    return decorate
