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

from storyboard.db.api import base as api_base
from storyboard.db import models

SUPPORTED_TYPES = {
    'project': models.Project,
    'project_group': models.ProjectGroup,
    'story': models.Story,
    'task': models.Task
}


def subscription_get(subscription_id):
    return api_base.entity_get(models.Subscription, subscription_id)


def subscription_get_all(**kwargs):
    return api_base.entity_get_all(models.Subscription,
                                   **kwargs)


def subscription_get_all_by_target(target_type, target_id):
    return api_base.entity_get_all(models.Subscription,
                                   target_type=target_type,
                                   target_id=target_id)


def subscription_get_resource(target_type, target_id):
    if target_type not in SUPPORTED_TYPES:
        return None

    return api_base.entity_get(SUPPORTED_TYPES[target_type], target_id)


def subscription_get_count(**kwargs):
    return api_base.entity_get_count(models.Subscription, **kwargs)


def subscription_create(values):
    return api_base.entity_create(models.Subscription, values)


def subscription_delete(subscription_id):
    subscription = subscription_get(subscription_id)

    if subscription:
        api_base.entity_hard_delete(models.Subscription, subscription_id)
