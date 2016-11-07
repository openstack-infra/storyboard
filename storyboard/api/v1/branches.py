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

from datetime import datetime
import pytz

from oslo_config import cfg
from pecan import abort
from pecan import response
from pecan import rest
from pecan.secure import secure
import six
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan

from storyboard._i18n import _
from storyboard.api.auth import authorization_checks as checks
from storyboard.api.v1.search import search_engine
from storyboard.api.v1 import validations
from storyboard.api.v1 import wmodels
from storyboard.common import decorators
from storyboard.common import exception as exc
from storyboard.db.api import branches as branches_api


CONF = cfg.CONF

SEARCH_ENGINE = search_engine.get_engine()


class BranchesController(rest.RestController):
    """REST controller for branches.
    """

    validation_post_schema = validations.BRANCHES_POST_SCHEMA
    validation_put_schema = validations.BRANCHES_PUT_SCHEMA

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose(wmodels.Branch, int)
    def get_one(self, branch_id):
        """Retrieve information about the given branch.

        Example::

          curl https://my.example.org/api/v1/branches/42

        :param branch_id: Branch ID.
        """

        branch = branches_api.branch_get(branch_id)

        if branch:
            return wmodels.Branch.from_db_model(branch)
        else:
            raise exc.NotFound(_("Branch %s not found") % branch_id)

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose([wmodels.Branch], int, int, wtypes.text, int, int,
                         wtypes.text, wtypes.text)
    def get_all(self, marker=None, limit=None, name=None, project_id=None,
                project_group_id=None, sort_field='id', sort_dir='asc'):
        """Retrieve a list of branches.

        Example::

          curl https://my.example.org/api/v1/branches

        :param marker: The resource id where the page should begin.
        :param limit: The number of branches to retrieve.
        :param name: Filter branches based on name.
        :param project_id: Filter branches based on project.
        :param project_group_id: Filter branches based on project group.
        :param sort_field: The name of the field to sort on.
        :param sort_dir: Sort direction for results (asc, desc).
        """
        # Boundary check on limit.
        if limit is not None:
            limit = max(0, limit)

        # Resolve the marker record.
        marker_branch = branches_api.branch_get(marker)

        branches = \
            branches_api.branch_get_all(marker=marker_branch,
                                        limit=limit,
                                        name=name,
                                        project_id=project_id,
                                        project_group_id=project_group_id,
                                        sort_field=sort_field,
                                        sort_dir=sort_dir)
        branches_count = \
            branches_api.branch_get_count(name=name,
                                          project_id=project_id,
                                          project_group_id=project_group_id)

        # Apply the query response headers.
        if limit:
            response.headers['X-Limit'] = str(limit)
        response.headers['X-Total'] = str(branches_count)
        if marker_branch:
            response.headers['X-Marker'] = str(marker_branch.id)

        return [wmodels.Branch.from_db_model(b) for b in branches]

    @decorators.db_exceptions
    @secure(checks.superuser)
    @wsme_pecan.wsexpose(wmodels.Branch, body=wmodels.Branch)
    def post(self, branch):
        """Create a new branch.

        Example::

          TODO

        :param branch: A branch within the request body.
        """

        branch_dict = branch.as_dict()

        # we can't create expired branch
        if branch.expiration_date or branch.expired:
            abort(400, _("Can't create expired branch."))

        result = branches_api.branch_create(branch_dict)
        return wmodels.Branch.from_db_model(result)

    @decorators.db_exceptions
    @secure(checks.superuser)
    @wsme_pecan.wsexpose(wmodels.Branch, int, body=wmodels.Branch)
    def put(self, branch_id, branch):
        """Modify this branch.

        Example::

          TODO

        :param branch_id: An ID of the branch.
        :param branch: A branch within the request body.
        """

        branch_dict = branch.as_dict(omit_unset=True)

        if "expiration_date" in six.iterkeys(branch_dict):
            abort(400, _("Can't change expiration date."))

        if "expired" in six.iterkeys(branch_dict):
            if branch_dict["expired"]:
                branch_dict["expiration_date"] = datetime.now(tz=pytz.utc)
            else:
                branch_dict["expiration_date"] = None

        if branch.project_id:
            original_branch = branches_api.branch_get(branch_id)

            if not original_branch:
                raise exc.NotFound(_("Branch %s not found") % branch_id)

            if branch.project_id != original_branch.project_id:
                abort(400, _("You can't associate branch %s "
                             "with another project.") % branch_id)

        result = branches_api.branch_update(branch_id, branch_dict)

        if result:
            return wmodels.Branch.from_db_model(result)
        else:
            raise exc.NotFound(_("Branch %s not found") % branch_id)
