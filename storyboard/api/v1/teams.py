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

from oslo_config import cfg
from pecan import abort
from pecan.decorators import expose
from pecan import response
from pecan import rest
from pecan.secure import secure
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan

from storyboard.api.auth import authorization_checks as checks
from storyboard.api.v1 import validations
from storyboard.api.v1 import wmodels
from storyboard.common import decorators
from storyboard.common import exception as exc
from storyboard.db.api import base as api_base
from storyboard.db.api import teams as teams_api
from storyboard.db.api import users as users_api
from storyboard.openstack.common.gettextutils import _  # noqas

CONF = cfg.CONF


class UsersSubcontroller(rest.RestController):
    """This controller should be used to list, add or remove users from a Team.
    """
    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose([wmodels.User], int)
    def get(self, team_id):
        """Get users inside a team.

        :param team_id: An ID of the team.
        """

        team = teams_api.team_get(team_id)

        if not team:
            raise exc.NotFound(_("Team %s not found") % team_id)

        users = [api_base._filter_non_public_fields(user, user._public_fields)
                 for user in team.users]
        return [wmodels.User.from_db_model(user) for user in users]

    @decorators.db_exceptions
    @secure(checks.superuser)
    @wsme_pecan.wsexpose(wmodels.User, int, int)
    def put(self, team_id, user_id):
        """Add a user to a team.

        :param team_id: An ID of the team.
        :param user_id: An ID of the user.
        """

        teams_api.team_add_user(team_id, user_id)
        user = users_api.user_get(user_id)
        user = api_base._filter_non_public_fields(user, user._public_fields)

        return wmodels.User.from_db_model(user)

    @decorators.db_exceptions
    @secure(checks.superuser)
    @wsme_pecan.wsexpose(None, int, int, status_code=204)
    def delete(self, team_id, user_id):
        """Delete a user from a team.

        :param team_id: An ID of the team.
        :param user_id: An ID of the user.
        """
        teams_api.team_delete_user(team_id, user_id)


class TeamsController(rest.RestController):
    """REST controller for Teams."""

    validation_post_schema = validations.TEAMS_POST_SCHEMA
    validation_put_schema = validations.TEAMS_PUT_SCHEMA

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose(wmodels.Team, int)
    def get_one_by_id(self, team_id):
        """Retrieve information about the given team.

        :param team_id: Team ID.
        """

        team = teams_api.team_get(team_id)

        if team:
            return wmodels.Team.from_db_model(team)
        else:
            raise exc.NotFound(_("Team %s not found") % team_id)

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose(wmodels.Team, wtypes.text)
    def get_one_by_name(self, team_name):
        """Retrieve information about the given team.

        :param team_name: Team name.
        """

        team = teams_api.team_get_by_name(team_name)

        if team:
            return wmodels.Team.from_db_model(team)
        else:
            raise exc.NotFound(_("Team %s not found") % team_name)

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose([wmodels.Team], int, int, int, wtypes.text,
                         wtypes.text, wtypes.text, wtypes.text)
    def get(self, marker=None, offset=None, limit=None, name=None,
            description=None, sort_field='id', sort_dir='asc'):
        """Retrieve a list of teams.

        :param offset: The offset at which to start the page.
        :param marker: The resource id where the page should begin.
        :param limit: The number of teams to retrieve.
        :param name: A string to filter the name by.
        :param description: A string to filter the description by.
        :param sort_field: The name of the field to sort on.
        :param sort_dir: Sort direction for results (asc, desc).
        """
        # Boundary check on limit.
        if limit is not None:
            limit = max(0, limit)

        # Resolve the marker record.
        marker_team = teams_api.team_get(marker)

        teams = teams_api.team_get_all(marker=marker_team,
                                       offset=offset,
                                       limit=limit,
                                       name=name,
                                       description=description,
                                       sort_field=sort_field,
                                       sort_dir=sort_dir)

        team_count = teams_api.team_get_count(name=name,
                                              description=description)

        # Apply the query response headers.
        if limit:
            response.headers['X-Limit'] = str(limit)
        response.headers['X-Total'] = str(team_count)
        if marker_team:
            response.headers['X-Marker'] = str(marker_team.id)
        if offset is not None:
            response.headers['X-Offset'] = str(offset)

        return [wmodels.Team.from_db_model(t) for t in teams]

    @decorators.db_exceptions
    @secure(checks.superuser)
    @wsme_pecan.wsexpose(wmodels.Team, body=wmodels.Team)
    def post(self, team):
        """Create a new team.

        :param team: a team within the request body.
        """
        result = teams_api.team_create(team.as_dict())
        return wmodels.Team.from_db_model(result)

    @decorators.db_exceptions
    @secure(checks.superuser)
    @wsme_pecan.wsexpose(wmodels.Team, int, body=wmodels.Team)
    def put(self, team_id, team):
        """Modify this team.

        :param team_id: An ID of the team.
        :param team: A team within the request body.
        """
        result = teams_api.team_update(team_id,
                                       team.as_dict(omit_unset=True))

        if result:
            return wmodels.Team.from_db_model(result)
        else:
            raise exc.NotFound(_("Team %s not found") % team_id)

    users = UsersSubcontroller()

    def _is_int(self, s):
        try:
            int(s)
            return True
        except ValueError:
            return False

    @expose()
    def _route(self, args, request):
        if request.method == 'GET' and len(args) > 0:
            # It's a request by a name or id
            first_token = args[0]
            if self._is_int(first_token):
                if len(args) > 1 and args[1] == "users":
                    # Route to users subcontroller
                    return super(TeamsController, self)._route(args, request)

                # Get by id
                return self.get_one_by_id, args
            else:
                # Get by name
                return self.get_one_by_name, ["/".join(args)]

        # Use default routing for all other requests
        return super(TeamsController, self)._route(args, request)

    @decorators.db_exceptions
    @secure(checks.superuser)
    @wsme_pecan.wsexpose(None, int, status_code=204)
    def delete(self, team_id):
        """Delete this team.

        :param team_id: An ID of the team.
        """
        try:
            teams_api.team_delete(team_id)
        except exc.NotFound as not_found_exc:
            abort(404, not_found_exc.message)
        except exc.NotEmpty as not_empty_exc:
            abort(400, not_empty_exc.message)
