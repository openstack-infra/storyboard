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
from wsme.exc import ClientSideError
import wsmeext.pecan as wsme_pecan

import storyboard.api.v1.wsme_models as wsme_models


class TeamsController(rest.RestController):

    _custom_actions = {
        "add_user": ["POST"]
    }

    @wsme_pecan.wsexpose(wsme_models.Team, unicode)
    def get_one(self, name):
        team = wsme_models.Team.get(name=name)
        if not team:
            raise ClientSideError("Team %s not found" % name,
                                  status_code=404)
        return team

    @wsme_pecan.wsexpose([wsme_models.Team])
    def get(self):
        teams = wsme_models.Team.get_all()
        return teams

    @wsme_pecan.wsexpose(wsme_models.Team, wsme_models.Team)
    def post(self, team):
        created_team = wsme_models.Team.create(wsme_entry=team)
        if not created_team:
            raise ClientSideError("Could not create a team")
        return created_team

    @wsme_pecan.wsexpose(wsme_models.Team, unicode, unicode)
    def add_user(self, team_name, username):
        updated_team = wsme_models.Team.add_user(team_name, username)
        if not updated_team:
            raise ClientSideError("Could not add user %s to team %s"
                                  % (username, team_name))
        return updated_team
