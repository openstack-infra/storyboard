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
# implied. See the License for the specific language governing permissions and
# limitations under the License.

from oslo_config import cfg

from storyboard._i18n import _

CONF = cfg.CONF

OAUTH_OPTS = [
    cfg.StrOpt('openid_url',
               default='https://login.launchpad.net/+openid',
               help='OpenId Authentication endpoint'),

    cfg.IntOpt("authorization_code_ttl",
               default=5 * 60,  # Five minutes
               help="Time in seconds before an authorization code expires"),

    cfg.IntOpt("access_token_ttl",
               default=60 * 60,  # One hour
               help="Time in seconds before an access_token expires"),

    cfg.IntOpt("refresh_token_ttl",
               default=60 * 60 * 24 * 7,  # One week
               help="Time in seconds before an refresh_token expires"),

    cfg.ListOpt("valid_oauth_clients",
               default=['storyboard.openstack.org', 'localhost'],
               help="A list of valid client id's that may connect to "
                    "StoryBoard.")
]

CONF.register_opts(OAUTH_OPTS, "oauth")


class ErrorMessages(object):
    """A list of error messages used in our OAuth Endpoint."""

    NO_RESPONSE_TYPE = _('You did not provide a response_type.')
    INVALID_RESPONSE_TYPE = _('response_type must be \'code\'')
    NO_CLIENT_ID = _('You did not provide a client_id.')
    INVALID_CLIENT_ID = _('You did not provide a valid client_id.')
    NO_REDIRECT_URI = _('You did not provide a redirect_uri.')
    INVALID_REDIRECT_URI = _('You did not provide a valid redirect_uri.')

    INVALID_SCOPE = _('scope must be \'user\'.')
    NO_SCOPE = _('You did not provide a scope.')

    OPEN_ID_TOKEN_INVALID = _('Our authorization server declined your '
                              'credentials.')

    INVALID_NO_EMAIL = _('Please permit access to your email address.')
    INVALID_NO_NAME = _('Please permit access to your name.')

    INVALID_TOKEN_GRANT_TYPE = _('Only grant types "authorization_code" and '
                                 '"refresh_token" are supported.')
