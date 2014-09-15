# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from oslo.config import cfg

from storyboard.migrate.launchpad.loader import LaunchpadLoader
from storyboard.openstack.common import log

IMPORT_OPTS = [
    cfg.StrOpt("from-project",
               default="storyboard",
               help="The name of the remote project to import."),
    cfg.StrOpt("to-project",
               default="openstack-infra/storyboard",
               help="The local destination project for the remote stories."),
    cfg.StrOpt("origin",
               default="launchpad",
               help="The origin system from which to import.")
]

CONF = cfg.CONF
LOG = log.getLogger(__name__)


def main():
    log.setup('storyboard')
    CONF.register_cli_opts(IMPORT_OPTS)
    CONF(project='storyboard')

    if CONF.origin is 'launchpad':
        loader = LaunchpadLoader(CONF.from_project, CONF.to_project)
        loader.run()
    else:
        print 'Unsupported import origin: %s' % CONF.origin
        return
