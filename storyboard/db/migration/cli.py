# -*- encoding: utf-8 -*-
#
# Copyright 2013 Hewlett-Packard Development Company, L.P.
# Copyright 2012 New Dream Network, LLC (DreamHost)
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import gettext
import os

from alembic import command as alembic_command
from alembic import config as alembic_config
from alembic import util as alembic_util
from oslo_config import cfg
from oslo_db import options
import six

from storyboard._i18n import _
from storyboard.db import projects_loader
from storyboard.db import superusers_loader

gettext.install('storyboard')

CONF = cfg.CONF


def do_alembic_command(config, cmd, *args, **kwargs):
    try:
        getattr(alembic_command, cmd)(config, *args, **kwargs)
    except alembic_util.CommandError as e:
        alembic_util.err(six.text_type(e))


def do_check_migration(config, cmd):
    do_alembic_command(config, 'branches')


def do_upgrade_downgrade(config, cmd):
    if not CONF.command.revision and not CONF.command.delta:
        raise SystemExit(_('You must provide a revision or relative delta'))

    revision = CONF.command.revision

    if CONF.command.delta:
        sign = '+' if CONF.command.name == 'upgrade' else '-'
        revision = sign + six.text_type(CONF.command.delta)
    else:
        revision = CONF.command.revision

    do_alembic_command(config, cmd, revision, sql=CONF.command.sql)


def do_stamp(config, cmd):
    do_alembic_command(config, cmd,
                       CONF.command.revision,
                       sql=CONF.command.sql)


def do_revision(config, cmd):
    do_alembic_command(config, cmd,
                       message=CONF.command.message,
                       autogenerate=CONF.command.autogenerate,
                       sql=CONF.command.sql)


def do_load_projects(config, cmd):
    projects_loader.do_load_models(CONF.command.file)


def do_load_superusers(config, cmd):
    superusers_loader.do_load_models(CONF.command.file)


def add_command_parsers(subparsers):
    for name in ['current', 'history', 'branches']:
        parser = subparsers.add_parser(name)
        parser.set_defaults(func=do_alembic_command)

    parser = subparsers.add_parser('check_migration')
    parser.set_defaults(func=do_check_migration)

    for name in ['upgrade', 'downgrade']:
        parser = subparsers.add_parser(name)
        parser.add_argument('--delta', type=int)
        parser.add_argument('--sql', action='store_true')
        parser.add_argument('revision', nargs='?')
        parser.set_defaults(func=do_upgrade_downgrade)

    parser = subparsers.add_parser('stamp')
    parser.add_argument('--sql', action='store_true')
    parser.add_argument('revision')
    parser.set_defaults(func=do_stamp)

    parser = subparsers.add_parser('revision')
    parser.add_argument('-m', '--message')
    parser.add_argument('--autogenerate', action='store_true')
    parser.add_argument('--sql', action='store_true')
    parser.set_defaults(func=do_revision)

    parser = subparsers.add_parser('load_projects')
    parser.add_argument('file', type=str)
    parser.set_defaults(func=do_load_projects)

    parser = subparsers.add_parser('load_superusers')
    parser.add_argument('file', type=str)
    parser.set_defaults(func=do_load_superusers)


command_opt = cfg.SubCommandOpt('command',
                                title='Command',
                                help=_('Available commands'),
                                handler=add_command_parsers)

CONF.register_cli_opt(command_opt)
CONF.register_opts(options.database_opts, 'database')


def get_alembic_config():
    config = alembic_config.Config(
        os.path.join(os.path.dirname(__file__), 'alembic.ini'))
    config.set_main_option('script_location',
                           'storyboard.db.migration:alembic_migrations')
    return config


def main():
    config = get_alembic_config()
    # attach the storyboard conf to the Alembic conf
    config.storyboard_config = CONF

    CONF(project='storyboard')
    CONF.command.func(config, CONF.command.name)
