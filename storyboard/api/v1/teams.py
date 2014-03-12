# Copyright (c) 2013 Mirantis Inc.
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


from pecan import rest
from pecan.secure import secure
from wsme.exc import ClientSideError
import wsmeext.pecan as wsme_pecan

from storyboard.api.auth import authorization_checks as checks
import storyboard.api.v1.wsme_models as wsme_models


class TeamsController(rest.RestController):
    """Manages teams."""

    _custom_actions = {
        "add_user": ["POST"]
    }

    @secure(checks.guest)
    @wsme_pecan.wsexpose(wsme_models.Team, unicode)
    def get_one(self, name):
        """Retrieve details about one team.

        :param name: unique name to identify the team.
        """
        team = wsme_models.Team.get(name=name)
        if not team:
            raise ClientSideError("Team %s not found" % name,
                                  status_code=404)
        return team

    @secure(checks.guest)
    @wsme_pecan.wsexpose([wsme_models.Team])
    def get(self):
        """Retrieve definitions of all of the teams."""
        teams = wsme_models.Team.get_all()
        return teams

    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wsme_models.Team, wsme_models.Team)
    def post(self, team):
        """Create a new team.

        :param team: a team within the request body.
        """
        created_team = wsme_models.Team.create(wsme_entry=team)
        if not created_team:
            raise ClientSideError("Could not create a team")
        return created_team

    # Note : Not a trivial check required here
    @secure(checks.authenticated)
    @wsme_pecan.wsexpose(wsme_models.Team, unicode, unicode)
    def add_user(self, team_name, username):
        """Associate a user with the team.

        :param team_name: unique name to identify the team.
        :param username: unique name to identify the user.
        """
        updated_team = wsme_models.Team.add_user(team_name, username)
        if not updated_team:
            raise ClientSideError("Could not add user %s to team %s"
                                  % (username, team_name))
        return updated_team
