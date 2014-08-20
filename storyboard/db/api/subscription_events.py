# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
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


def subscription_events_get(subscription_event_id):
    return api_base.entity_get(models.SubscriptionEvents,
                               subscription_event_id)


def subscription_events_get_all(**kwargs):
    return api_base.entity_get_all(models.SubscriptionEvents,
                                   **kwargs)


def subscription_events_get_count(**kwargs):
    return api_base.entity_get_count(models.SubscriptionEvents, **kwargs)


def subscription_events_create(values):
    return api_base.entity_create(models.SubscriptionEvents, values)


def subscription_events_delete(subscription_event_id):
    subscription = subscription_events_get(subscription_event_id)

    if subscription:
        api_base.entity_hard_delete(models.SubscriptionEvents,
                                    subscription_event_id)
