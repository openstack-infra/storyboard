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

from storyboard.db.api import base as api_base
from storyboard.db import models


def milestone_get(milestone_id):
    return api_base.entity_get(models.Milestone, milestone_id)


def milestone_get_all(marker=None, limit=None, sort_field=None, sort_dir=None,
                      **kwargs):
    return api_base.entity_get_all(models.Milestone,
                                   marker=marker,
                                   limit=limit,
                                   sort_field=sort_field,
                                   sort_dir=sort_dir,
                                   **kwargs)


def milestone_get_count(**kwargs):
    return api_base.entity_get_count(models.Milestone, **kwargs)


def milestone_create(values):
    return api_base.entity_create(models.Milestone, values)


def milestone_update(milestone_id, values):
    return api_base.entity_update(models.Milestone, milestone_id, values)
