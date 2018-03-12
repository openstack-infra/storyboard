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

from __future__ import print_function
import sys

from oslo_config import cfg
from oslo_log import log

from storyboard.db.api import base as db_api
from storyboard.migrate.launchpad.loader import LaunchpadLoader

IMPORT_OPTS = [
    cfg.StrOpt("from-project",
               default="storyboard",
               help="The name of the remote project to import."),
    cfg.StrOpt("to-project",
               default="openstack-infra/storyboard",
               help="The local destination project for the remote stories."),
    cfg.StrOpt("origin",
               default="launchpad",
               help="The origin system from which to import."),
    cfg.IntOpt("auto-increment",
               default=None,
               help="Optionally set the auto-increment on the stories table."),
    cfg.ListOpt("only-tags",
                default=[],
                help="Include only the bugs with specified tags."),
    cfg.ListOpt("exclude-tags",
                default=[],
                help="Exclude the bugs with the specified tags.")
]

CONF = cfg.CONF
LOG = log.getLogger(__name__)


def main():
    CONF.register_cli_opts(IMPORT_OPTS)
    try:
        log.register_options(CONF)
    except cfg.ArgsAlreadyParsedError:
        pass
    log.setup(CONF, 'storyboard')
    CONF(project='storyboard')

    # only_tags and exclude_tags are mutually exclusive
    if CONF.only_tags and CONF.exclude_tags:
        print('ERROR: only-tags and exclude-tags are mutually exclusive',
              file=sys.stderr)
        exit(1)

    # If the user requested an autoincrement value, set that before we start
    # importing things. Note that mysql will automatically set the
    # autoincrement to the next-available id equal to or larger than the
    # requested one.
    auto_increment = CONF.auto_increment
    if auto_increment:
        print('Setting stories.AUTO_INCREMENT to %d' % (auto_increment,))
        session = db_api.get_session(in_request=False)
        session.execute('ALTER TABLE stories AUTO_INCREMENT = %d;'
                        % (auto_increment,))

    if CONF.origin is 'launchpad':
        loader = LaunchpadLoader(CONF.from_project, CONF.to_project,
                                 set(CONF.only_tags), set(CONF.exclude_tags))
        loader.run()
    else:
        print('Unsupported import origin: %s' % CONF.origin)
        return
