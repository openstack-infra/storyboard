# Copyright (c) 2014 Mirantis Inc.
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

from storyboard.db.api import base as api_base
from storyboard.db import models


def project_get(project_id):
    return api_base.entity_get(models.Project, project_id)


def project_get_by_name(name):
    query = api_base.model_query(models.Project, api_base.get_session())
    return query.filter_by(name=name).first()


def project_get_all(marker=None, limit=None, sort_field=None, sort_dir=None,
                    **kwargs):
    return api_base.entity_get_all(models.Project,
                                   is_active=True,
                                   marker=marker,
                                   limit=limit,
                                   sort_field=sort_field,
                                   sort_dir=sort_dir,
                                   **kwargs)


def project_get_count(**kwargs):
    return api_base.entity_get_count(models.Project, is_active=True, **kwargs)


def project_create(values):
    return api_base.entity_create(models.Project, values)


def project_update(project_id, values):
    return api_base.entity_update(models.Project, project_id, values)
