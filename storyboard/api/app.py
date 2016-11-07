# Copyright (c) 2013 Mirantis Inc.
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

import os

from oslo_config import cfg
from oslo_log import _options
from oslo_log import log
import pecan
from wsgiref import simple_server

from storyboard._i18n import _LI
from storyboard.api import config as api_config
from storyboard.api.middleware.cors_middleware import CORSMiddleware
from storyboard.api.middleware import session_hook
from storyboard.api.middleware import token_middleware
from storyboard.api.middleware import user_id_hook
from storyboard.api.middleware import validation_hook
from storyboard.api.v1.search import impls as search_engine_impls
from storyboard.api.v1.search import search_engine
from storyboard.notifications.notification_hook import NotificationHook
from storyboard.plugin.scheduler import initialize_scheduler
from storyboard.plugin.user_preferences import initialize_user_preferences

CONF = cfg.CONF

LOG = log.getLogger(__name__)

try:
    log.register_options(CONF)
except cfg.ArgsAlreadyParsedError:
    pass

API_OPTS = [
    cfg.StrOpt('bind_host',
               default='0.0.0.0',
               help='API host'),
    cfg.IntOpt('bind_port',
               default=8080,
               help='API port'),
    cfg.BoolOpt('enable_notifications',
               default=False,
               help='Enable Notifications'),
    cfg.BoolOpt('enable_editable_comments',
               default=False,
               help='Enable editing and deletion of comments')
]
CORS_OPTS = [
    cfg.ListOpt('allowed_origins',
                default=None,
                help='List of permitted CORS origins.'),
    cfg.IntOpt('max_age',
               default=3600,
               help='Maximum cache age of CORS preflight requests.')
]
CONF.register_opts(API_OPTS)
CONF.register_opts(CORS_OPTS, 'cors')


def get_pecan_config():
    # Set up the pecan configuration
    filename = api_config.__file__.replace('.pyc', '.py')
    return pecan.configuration.conf_from_file(filename)


def setup_app(pecan_config=None):
    if not pecan_config:
        pecan_config = get_pecan_config()

    # Setup logging
    cfg.set_defaults(_options.log_opts,
                     default_log_levels=[
                         'storyboard=INFO',
                         'storyboard.openstack.common.db=WARN',
                         'sqlalchemy=WARN'
                     ])
    log.setup(CONF, 'storyboard')

    hooks = [
        session_hook.DBSessionHook(),
        user_id_hook.UserIdHook(),
        validation_hook.ValidationHook()
    ]

    # Setup search engine
    search_engine_name = CONF.search_engine
    search_engine_cls = search_engine_impls.ENGINE_IMPLS[search_engine_name]
    search_engine.set_engine(search_engine_cls())

    # Load user preference plugins
    initialize_user_preferences()

    # Initialize scheduler
    initialize_scheduler()

    # Setup notifier
    if CONF.enable_notifications:
        hooks.append(NotificationHook())

    app = pecan.make_app(
        pecan_config.app.root,
        debug=CONF.debug,
        hooks=hooks,
        force_canonical=getattr(pecan_config.app, 'force_canonical', True),
        guess_content_type_from_ext=False
    )

    app = token_middleware.AuthTokenMiddleware(app)

    # Setup CORS
    if CONF.cors.allowed_origins:
        app = CORSMiddleware(app,
                             allowed_origins=CONF.cors.allowed_origins,
                             allowed_methods=['GET', 'POST', 'PUT', 'DELETE',
                                              'OPTIONS'],
                             allowed_headers=['origin', 'authorization',
                                              'accept', 'x-total', 'x-limit',
                                              'x-marker', 'x-client',
                                              'content-type'],
                             max_age=CONF.cors.max_age)

    return app


def start():
    CONF(project='storyboard')

    api_root = setup_app()

    # Create the WSGI server and start it
    host = cfg.CONF.bind_host
    port = cfg.CONF.bind_port

    srv = simple_server.make_server(host, port, api_root)

    LOG.info(_LI('Starting server in PID %s') % os.getpid())
    LOG.info(_LI("Configuration:"))
    if host == '0.0.0.0':
        LOG.info(_LI(
            'serving on 0.0.0.0:%(port)s, view at http://127.0.0.1:%(port)s')
            % ({'port': port}))
    else:
        LOG.info(_LI("serving on http://%(host)s:%(port)s") % (
                 {'host': host, 'port': port}))

    srv.serve_forever()

if __name__ == '__main__':
    start()
