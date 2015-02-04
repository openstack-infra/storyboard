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

import json
from urllib import urlencode
from urlparse import parse_qsl

import functools
from pecan import abort
from pecan import redirect
from pecan import response
import rfc3987

from storyboard.common import exception as exc
from storyboard.openstack.common.gettextutils import _  # noqa


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
            error_description = o_exc.message or _("No details available.")

            # If we have a redirect URL, build the error redirect.
            if o_exc.redirect_uri:
                # Split the redirect_url apart
                parts = rfc3987.parse(o_exc.redirect_uri, 'URI')

                # Add the error and error_description
                params = parse_qsl(parts['query']) if parts['query'] else []
                params.append(('error', error))
                params.append(('error_description', error_description))

                # Overwrite the old query params and reconstruct the URL
                parts['query'] = urlencode(params)
                location = rfc3987.compose(**parts)

                redirect(location)
            else:
                error_body = {
                    'error': error,
                    'error_description': error_description
                }
                response.body = json.dumps(error_body)
                abort(o_exc.code, error_description)

    return decorate
