# Copyright (c) 2013 Mirantis Inc.
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

import warnings
import yaml

from oslo.config import cfg
from sqlalchemy.exc import SADeprecationWarning

from storyboard.common.custom_types import NameType
from storyboard.db.api import base as db_api
from storyboard.db.models import Project
from storyboard.db.models import ProjectGroup
from storyboard.openstack.common.gettextutils import _LW  # noqa
from storyboard.openstack.common import log


warnings.simplefilter("ignore", SADeprecationWarning)
CONF = cfg.CONF
LOG = log.getLogger(__name__)


def do_load_models(filename):
    config_file = open(filename)
    session = db_api.get_session(autocommit=False)
    projects_list = yaml.load(config_file)

    project_groups = list()

    # Create all the projects.
    for project in projects_list:

        if not project.get('use-storyboard'):
            continue

        project_instance = _get_project(project, session)
        project_instance_groups = list()

        if not project_instance:
            continue

        groups = project.get("groups") or []
        for group_name in groups:
            group_instance = _get_project_group(group_name, session)
            project_instance_groups.append(group_instance)

            if group_instance not in project_groups:
                project_groups.append(group_instance)

        # Brute force diff
        groups_to_remove = set(project_instance.project_groups) - set(
            project_instance_groups)
        groups_to_add = set(project_instance_groups) - set(
            project_instance.project_groups)

        for group in groups_to_remove:
            project_instance.project_groups.remove(group)

        for group in groups_to_add:
            project_instance.project_groups.append(group)

        if len(groups_to_remove) + len(groups_to_add) > 0:
            session.add(project_instance)

    # Now, go through all groups that were not explicitly listed and delete
    # them.
    project_groups_to_delete = list()
    current_groups = session.query(ProjectGroup)
    for current_group in current_groups:
        if current_group not in project_groups:
            project_groups_to_delete.append(current_group)

    for group in project_groups_to_delete:
        session.delete(group)

    session.commit()


def _get_project(project, session):
    validator = NameType()
    name = unicode(project['project'])
    if 'description' in project:
        description = unicode(project['description'])
    else:
        description = ''

    try:
        validator.validate(name)
    except Exception:
        # Skipping invalid project names
        LOG.warn(_LW("Project %s was not loaded. Validation failed.")
                 % [name, ])
        return None

    db_project = session.query(Project) \
        .filter_by(name=name).first()
    if not db_project:
        db_project = Project()
        db_project.name = name
        db_project.description = description
        db_project.groups = []

    session.add(db_project)

    return db_project


def _get_project_group(project_group_name, session):
    db_project_group = session.query(ProjectGroup) \
        .filter_by(name=project_group_name).first()

    if not db_project_group:
        db_project_group = ProjectGroup()
        db_project_group.title = project_group_name
        db_project_group.name = project_group_name

        session.add(db_project_group)

    return db_project_group
