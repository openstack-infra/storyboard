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


def task_get(task_id):
    return api_base.entity_get(models.Task, task_id)


def task_get_all(marker=None, limit=None, **kwargs):
    return api_base.entity_get_all(models.Task,
                                   marker=marker,
                                   limit=limit,
                                   **kwargs)


def task_get_count(**kwargs):
    return api_base.entity_get_count(models.Task, **kwargs)


def task_create(values):
    return api_base.entity_create(models.Task, values)


def task_update(task_id, values):
    return api_base.entity_update(models.Task, task_id, values)


def task_delete(task_id):
    task = task_get(task_id)

    if task:
        api_base.entity_hard_delete(models.Task, task_id)
