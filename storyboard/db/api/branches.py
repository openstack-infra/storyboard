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

from storyboard._i18n import _
from storyboard.common import exception as exc
from storyboard.db.api import base as api_base
from storyboard.db import models


def branch_get(branch_id):
    return api_base.entity_get(models.Branch, branch_id)


def branch_get_all(marker=None, limit=None, sort_field=None, sort_dir=None,
                   project_group_id=None, **kwargs):
    if not sort_field:
        sort_field = 'id'
    if not sort_dir:
        sort_dir = 'asc'

    query = branch_build_query(project_group_id=project_group_id,
                               **kwargs)

    query = api_base.paginate_query(query=query,
                                    model=models.Branch,
                                    limit=limit,
                                    sort_key=sort_field,
                                    marker=marker,
                                    sort_dir=sort_dir)

    return query.all()


def branch_get_count(project_group_id=None, **kwargs):
    query = branch_build_query(project_group_id=project_group_id,
                               **kwargs)

    return query.count()


def branch_create(values):
    return api_base.entity_create(models.Branch, values)


def branch_update(branch_id, values):
    return api_base.entity_update(models.Branch, branch_id, values)


def branch_build_query(project_group_id, **kwargs):
    query = api_base.model_query(models.Branch)

    if project_group_id:
        query = query.join(models.Project.project_groups) \
            .filter(models.ProjectGroup.id == project_group_id)

    query = api_base.apply_query_filters(query=query, model=models.Branch,
                                         **kwargs)

    return query


def branch_get_master_branch(project_id):
    query = api_base.model_query(models.Branch)
    query = query.filter_by(project_id=project_id, name='master').first()

    if not query:
        raise exc.NotFound(_("Master branch of project %d not found.")
                           % project_id)

    return query
