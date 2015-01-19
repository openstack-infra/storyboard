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
from storyboard.plugin.user_preferences import PREFERENCE_DEFAULTS


def user_get(user_id, filter_non_public=False):
    entity = api_base.entity_get(models.User, user_id,
                                 filter_non_public=filter_non_public)

    return entity


def user_get_all(marker=None, limit=None, filter_non_public=False,
                 sort_field=None, sort_dir=None, **kwargs):
    return api_base.entity_get_all(models.User,
                                   marker=marker,
                                   limit=limit,
                                   filter_non_public=filter_non_public,
                                   sort_field=sort_field,
                                   sort_dir=sort_dir,
                                   **kwargs)


def user_get_count(**kwargs):
    return api_base.entity_get_count(models.User, **kwargs)


def user_get_by_openid(openid):
    query = api_base.model_query(models.User, api_base.get_session())
    return query.filter_by(openid=openid).first()


def user_create(values):
    return api_base.entity_create(models.User, values)


def user_update(user_id, values):
    return api_base.entity_update(models.User, user_id, values)


def user_get_preferences(user_id):
    preferences = api_base.entity_get_all(models.UserPreference,
                                          user_id=user_id)

    pref_dict = dict()
    for pref in preferences:
        pref_dict[pref.key] = pref.cast_value

    # Decorate with plugin defaults.
    for key in PREFERENCE_DEFAULTS:
        if key not in pref_dict:
            pref_dict[key] = PREFERENCE_DEFAULTS[key]

    return pref_dict


def user_update_preferences(user_id, preferences):
    for key in preferences:
        value = preferences[key]
        prefs = api_base.entity_get_all(models.UserPreference,
                                       user_id=user_id,
                                       key=key)

        if prefs:
            pref = prefs[0]
        else:
            pref = None

        # If the preference exists and it's null.
        if pref and value is None:
            api_base.entity_hard_delete(models.UserPreference, pref.id)
            continue

        # If the preference exists and has a new value.
        if pref and value and pref.cast_value != value:
            pref.cast_value = value
            api_base.entity_update(models.UserPreference, pref.id, dict(pref))
            continue

        # If the preference does not exist and a new value exists.
        if not pref and value:
            api_base.entity_create(models.UserPreference, {
                'user_id': user_id,
                'key': key,
                'cast_value': value
            })

    return user_get_preferences(user_id)
