# Copyright (c) 2014 Mirantis Inc.
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


import datetime
import pytz
from storyboard.common.master_branch_helper import MasterBranchHelper
from storyboard.db.api import base as api_base
from storyboard.db.api import branches as branches_api
from storyboard.db import models


def project_get(project_id):
    return api_base.entity_get(models.Project, project_id)


def project_get_by_name(name):
    query = api_base.model_query(models.Project, api_base.get_session())
    return query.filter_by(name=name).first()


def project_get_all(marker=None, offset=None, limit=None, sort_field=None,
                    sort_dir=None, project_group_id=None, subscriber_id=None,
                    **kwargs):
    # Sanity checks, in case someone accidentally explicitly passes in 'None'
    if not sort_field:
        sort_field = 'id'
    if not sort_dir:
        sort_dir = 'asc'

    # Construct the query
    query = project_build_query(project_group_id=project_group_id,
                                **kwargs)

    # Filter by subscriber ID
    if subscriber_id is not None:
        subs = api_base.model_query(models.Subscription)
        subs = api_base.apply_query_filters(query=subs,
                                            model=models.Subscription,
                                            user_id=subscriber_id)
        # Filter by exact match, to avoid matching "project_group"
        subs = subs.filter(models.Subscription.target_type == 'project')
        subs = subs.subquery()
        query = query.join(subs, subs.c.target_id == models.Project.id)

    query = api_base.paginate_query(query=query,
                                    model=models.Project,
                                    limit=limit,
                                    sort_key=sort_field,
                                    marker=marker,
                                    offset=offset,
                                    sort_dir=sort_dir)

    # Execute the query
    return query.all()


def project_get_count(project_group_id=None, subscriber_id=None, **kwargs):
    # Construct the query
    query = project_build_query(project_group_id=project_group_id,
                                **kwargs)

    # Filter by subscriber ID
    if subscriber_id is not None:
        subs = api_base.model_query(models.Subscription)
        subs = api_base.apply_query_filters(query=subs,
                                            model=models.Subscription,
                                            target_type='project',
                                            user_id=subscriber_id)
        subs = subs.subquery()
        query = query.join(subs, subs.c.target_id == models.Project.id)

    return query.count()


def project_create(values):
    # Create project and 'master' branch for him
    project = api_base.entity_create(models.Project, values)
    master_branch = MasterBranchHelper(project["id"])
    branches_api.branch_create(master_branch.as_dict())
    return project


def project_update(project_id, values):
    return api_base.entity_update(models.Project, project_id, values)


def project_update_updated_at(project_id):
    session = api_base.get_session()
    project = project_get(project_id)
    if project:
        with session.begin(subtransactions=True):
            project.updated_at = datetime.datetime.now(tz=pytz.utc)
            session.add(project)
        session.expunge(project)


def project_build_query(project_group_id, **kwargs):
    # Construct the query
    query = api_base.model_query(models.Project)

    if project_group_id:
        query = query.join(models.Project.project_groups) \
            .filter(models.ProjectGroup.id == project_group_id)

    # Sanity check on input parameters
    query = api_base.apply_query_filters(query=query, model=models.Project,
                                         **kwargs)

    return query
