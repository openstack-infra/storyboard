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
from storyboard.db.api import milestones as milestones_api


CONF = cfg.CONF

SEARCH_ENGINE = search_engine.get_engine()


class MilestonesController(rest.RestController):
    """REST controller for milestones.
    """

    validation_post_schema = validations.MILESTONES_POST_SCHEMA
    validation_put_schema = validations.MILESTONES_PUT_SCHEMA

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose(wmodels.Milestone, int)
    def get_one(self, milestone_id):
        """Retrieve information about the given milestone.

        :param milestone_id: Milestone ID.
        """

        milestones = milestones_api.milestone_get(milestone_id)

        if milestones:
            return wmodels.Milestone.from_db_model(milestones)
        else:
            raise exc.NotFound(_("Milestone %s not found") % milestone_id)

    @decorators.db_exceptions
    @secure(checks.guest)
    @wsme_pecan.wsexpose([wmodels.Milestone], int, int, wtypes.text, int,
                         wtypes.text, wtypes.text)
    def get_all(self, marker=None, limit=None, name=None, branch_id=None,
                sort_field='id', sort_dir='asc'):
        """Retrieve a list of milestones.

        :param marker: The resource id where the page should begin.
        :param limit: The number of milestones to retrieve.
        :param name: Filter milestones based on name.
        :param branch_id: Filter milestones based on branch_id.
        :param sort_field: The name of the field to sort on.
        :param sort_dir: Sort direction for results (asc, desc).
        """
        # Boundary check on limit.
        if limit is not None:
            limit = max(0, limit)

        # Resolve the marker record.
        marker_milestone = milestones_api.milestone_get(marker)

        milestones = \
            milestones_api.milestone_get_all(marker=marker_milestone,
                                             limit=limit,
                                             name=name,
                                             branch_id=branch_id,
                                             sort_field=sort_field,
                                             sort_dir=sort_dir)
        milestones_count = \
            milestones_api.milestone_get_count(
                name=name,
                branch_id=branch_id)

        # Apply the query response headers.
        if limit:
            response.headers['X-Limit'] = str(limit)
        response.headers['X-Total'] = str(milestones_count)
        if marker_milestone:
            response.headers['X-Marker'] = str(marker_milestone.id)

        return [wmodels.Milestone.from_db_model(m) for m in milestones]

    @decorators.db_exceptions
    @secure(checks.superuser)
    @wsme_pecan.wsexpose(wmodels.Milestone, body=wmodels.Milestone)
    def post(self, milestone):
        """Create a new milestone.

        :param milestone: A milestone within the request body.
        """

        # we can't create expired milestones
        if milestone.expiration_date or milestone.expired:
            abort(400, _("Can't create expired milestone."))

        result = milestones_api.milestone_create(milestone.as_dict())
        return wmodels.Milestone.from_db_model(result)

    @decorators.db_exceptions
    @secure(checks.superuser)
    @wsme_pecan.wsexpose(wmodels.Milestone, int, body=wmodels.Milestone)
    def put(self, milestone_id, milestone):
        """Modify this milestone.

        :param milestone_id: An ID of the milestone.
        :param milestone: A milestone within the request body.
        """

        milestone_dict = milestone.as_dict(omit_unset=True)

        if milestone.expiration_date:
            abort(400, _("Can't change expiration date."))

        if "expired" in six.iterkeys(milestone_dict):
            if milestone_dict["expired"]:
                milestone_dict["expiration_date"] = datetime.now(tz=pytz.utc)
            else:
                milestone_dict["expiration_date"] = None

        if milestone.branch_id:
            original_milestone = milestones_api.milestone_get(milestone_id)

            if not original_milestone:
                raise exc.NotFound(_("Milestone %s not found") % milestone_id)

            if milestone.branch_id != original_milestone.branch_id:
                abort(400, _("You can't associate milestone %s "
                             "with another branch.") % milestone_id)

        result = milestones_api.milestone_update(milestone_id, milestone_dict)

        if result:
            return wmodels.Milestone.from_db_model(result)
        else:
            raise exc.NotFound(_("Milestone %s not found") % milestone_id)
