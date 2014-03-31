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

from oslo.config import cfg
import pecan
from wsgiref import simple_server

from storyboard.api.auth.token_storage import impls as storage_impls
from storyboard.api.auth.token_storage import storage
from storyboard.api import config as api_config
from storyboard.api.middleware import token_middleware
from storyboard.api.middleware import user_id_hook
from storyboard.openstack.common.gettextutils import _  # noqa
from storyboard.openstack.common import log

CONF = cfg.CONF
LOG = log.getLogger(__name__)

API_OPTS = [
    cfg.StrOpt('bind_host',
               default='0.0.0.0',
               help='API host'),
    cfg.IntOpt('bind_port',
               default=8080,
               help='API port')
]
CONF.register_opts(API_OPTS)


def get_pecan_config():
    # Set up the pecan configuration
    filename = api_config.__file__.replace('.pyc', '.py')
    return pecan.configuration.conf_from_file(filename)


def setup_app(pecan_config=None):
    if not pecan_config:
        pecan_config = get_pecan_config()

    # Setup token storage
    token_storage_type = CONF.token_storage_type
    storage_cls = storage_impls.STORAGE_IMPLS[token_storage_type]
    storage.set_storage(storage_cls())

    app = pecan.make_app(
        pecan_config.app.root,
        debug=CONF.debug,
        hooks=[user_id_hook.UserIdHook()],
        force_canonical=getattr(pecan_config.app, 'force_canonical', True),
        guess_content_type_from_ext=False
    )

    cfg.set_defaults(log.log_opts,
                     default_log_levels=[
                         'storyboard=INFO',
                         'sqlalchemy=WARN'
                     ])
    log.setup('storyboard')

    return app


def start():
    CONF(project='storyboard')

    api_root = setup_app()

    # Create the WSGI server and start it
    host = cfg.CONF.bind_host
    port = cfg.CONF.bind_port

    api_root = token_middleware.AuthTokenMiddleware(api_root)
    srv = simple_server.make_server(host, port, api_root)

    LOG.info(_('Starting server in PID %s') % os.getpid())
    LOG.info(_("Configuration:"))
    if host == '0.0.0.0':
        LOG.info(_(
            'serving on 0.0.0.0:%(port)s, view at http://127.0.0.1:%(port)s')
            % ({'port': port}))
    else:
        LOG.info(_("serving on http://%(host)s:%(port)s") % (
                 {'host': host, 'port': port}))

    srv.serve_forever()
