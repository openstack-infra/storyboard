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

import six
import warnings
import yaml

from oslo.config import cfg
from sqlalchemy.exc import SADeprecationWarning
from storyboard.db.api import base as db_api

from storyboard.db.models import Project
from storyboard.db.models import ProjectGroup


warnings.simplefilter("ignore", SADeprecationWarning)
CONF = cfg.CONF


def do_load_models(filename):

    config_file = open(filename)
    projects_list = yaml.load(config_file)

    project_groups = dict()

    for project in projects_list:
        if not project.get('use-storyboard'):
            continue
        group_name = project.get("group") or "default"
        if group_name not in project_groups:
            project_groups[group_name] = list()

        project_name = project.get("project")
        project_description = project.get("description")

        project_groups[group_name].append({"name": project_name,
                                           "description": project_description})

    session = db_api.get_session()

    with session.begin():
        for project_group_name, projects in six.iteritems(project_groups):
            db_project_group = session.query(ProjectGroup)\
                .filter_by(name=project_group_name).first()
            if not db_project_group:
                db_project_group = ProjectGroup()
                db_project_group.name = project_group_name
                db_project_group.projects = []

            for project in projects:
                db_project = session.query(Project)\
                    .filter_by(name=project["name"]).first()
                if not db_project:
                    db_project = Project()
                    db_project.name = project["name"]

                if project['description']:
                    project['description'] = unicode(project["description"])

                db_project.description = project["description"]
                session.add(db_project)

                db_project_group.projects.append(db_project)

            session.add(db_project_group)
