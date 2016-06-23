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


def user_get(user_id, filter_non_public=False, session=None):
    entity = api_base.entity_get(models.User, user_id,
                                 filter_non_public=filter_non_public,
                                 session=session)

    return entity


def _build_user_query(full_name=None, email=None, openid=None):
    query = api_base.model_query(models.User)

    query = api_base.apply_query_filters(query=query,
                                         model=models.User,
                                         full_name=full_name)

    if email:
        query = query.filter(models.User.email == email)

    if openid:
        query = query.filter(models.User.openid == openid)

    return query


def user_get_all(marker=None, offset=None, limit=None,
                 filter_non_public=False, sort_field=None, sort_dir=None,
                 full_name=None, email=None, openid=None,
                 **kwargs):
    query = _build_user_query(full_name=full_name,
                              email=email,
                              openid=openid)

    query = api_base.paginate_query(query=query,
                                    model=models.User,
                                    limit=limit,
                                    marker=marker,
                                    offset=offset,
                                    sort_key=sort_field,
                                    sort_dir=sort_dir)

    users = query.all()
    if len(users) > 0 and filter_non_public:
        sample_user = users[0]
        public_fields = getattr(sample_user, "_public_fields", [])

        users = [api_base._filter_non_public_fields(user, public_fields)
                 for user in users]

    return users


def user_get_count(**kwargs):
    return api_base.entity_get_count(models.User, **kwargs)


def user_get_by_openid(openid):
    query = api_base.model_query(models.User, api_base.get_session())
    return query.filter_by(openid=openid).first()


def user_create(values):
    return api_base.entity_create(models.User, values)


def user_update(user_id, values, filter_non_public=False):
    return api_base.entity_update(models.User, user_id, values,
                                  filter_non_public=filter_non_public)


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

        matching_prefs = []
        if prefs:
            for p in prefs:
                if p.key == key:
                    # FIXME: We create a list here because there appears to
                    # currently be a bug which means that each preference may
                    # appear more than once per-user. We should fix that once
                    # we discover the cause.
                    matching_prefs.append(p)
        else:
            pref = None

        for pref in matching_prefs:
            # If the preference exists and it's null.
            if pref and value is None:
                api_base.entity_hard_delete(models.UserPreference, pref.id)
                continue

            # If the preference exists and has a new value.
            if pref and value is not None and pref.cast_value != value:
                pref.cast_value = value
                api_base.entity_update(
                    models.UserPreference, pref.id, dict(pref))
                continue

        # If the preference does not exist and a new value exists.
        if not matching_prefs and value is not None:
            api_base.entity_create(models.UserPreference, {
                'user_id': user_id,
                'key': key,
                'cast_value': value
            })

    return user_get_preferences(user_id)
