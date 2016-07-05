# Copyright (c) 2013 Hewlett-Packard Development Company, L.P.
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

from oslo_config import cfg
from pbr.version import VersionInfo
from pecan import rest
from pecan.secure import secure
from storyboard.api.auth import authorization_checks as checks
from storyboard.api.v1 import wmodels
import wsmeext.pecan as wsme_pecan

CONF = cfg.CONF


class SystemInfoController(rest.RestController):
    """REST controller for sysinfo endpoint.

    Provides Get methods for System information.
    """

    @secure(checks.guest)
    @wsme_pecan.wsexpose(wmodels.SystemInfo)
    def get(self):
        """Retrieve the Storyboard system information.

        Example::

          curl https://my.example.org/api/v1/systeminfo

        """
        sb_ver = VersionInfo('storyboard')

        return wmodels.SystemInfo(version=sb_ver.version_string())
