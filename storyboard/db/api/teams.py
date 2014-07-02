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

from sqlalchemy.orm import subqueryload
from wsme.exc import ClientSideError

from storyboard.common import exception as exc
from storyboard.db.api import base as api_base
from storyboard.db.api import users
from storyboard.db import models


def _entity_get(id, session=None):
    if not session:
        session = api_base.get_session()
    query = session.query(models.Team)\
        .options(subqueryload(models.Team.users))\
        .filter_by(id=id)

    return query.first()


def team_get(team_id):
    return _entity_get(team_id)


def team_get_all(marker=None, limit=None, sort_field=None,
                 sort_dir=None, **kwargs):
    return api_base.entity_get_all(models.Team,
                                   marker=marker,
                                   limit=limit,
                                   sort_field=sort_field,
                                   sort_dir=sort_dir,
                                   **kwargs)


def team_get_count(**kwargs):
    return api_base.entity_get_count(models.Team, **kwargs)


def team_create(values):
    return api_base.entity_create(models.Team, values)


def team_update(team_id, values):
    return api_base.entity_update(models.Team, team_id,
                                  values)


def team_add_user(team_id, user_id):
    session = api_base.get_session()

    with session.begin():
        team = _entity_get(team_id, session)
        if team is None:
            raise exc.NotFound("%s %s not found" % ("Team", team_id))

        user = users.user_get(user_id)
        if user is None:
            raise exc.NotFound("%s %s not found" % ("User", user_id))

        if user_id in [u.id for u in team.users]:
            raise ClientSideError("The User %d is already in Team %d" %
                                  (user_id, team_id))

        team.users.append(user)
        session.add(team)

    return team


def team_delete_user(team_id, user_id):
    session = api_base.get_session()

    with session.begin():
        team = _entity_get(team_id, session)
        if team is None:
            raise exc.NotFound("%s %s not found" % ("Team", team_id))

        user = users.user_get(user_id)
        if user is None:
            raise exc.NotFound("%s %s not found" % ("User", user_id))

        if user_id not in [u.id for u in team.users]:
            raise ClientSideError("The User %d is not in Team %d" %
                                  (user_id, team_id))

        user_entry = [u for u in team.users if u.id == user_id][0]
        team.users.remove(user_entry)
        session.add(team)

    return team
