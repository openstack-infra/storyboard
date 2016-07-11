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


class MasterBranchHelper(object):
    name = "master"
    project_id = None
    expired = False
    expiration_date = None
    autocreated = False
    restricted = True

    def __init__(self, project_id):
        self.project_id = project_id

    def as_dict(self):
        master_branch_dict = {
            "name": self.name,
            "project_id": self.project_id,
            "expired": self.expired,
            "expiration_date": self.expiration_date,
            "autocreated": self.autocreated,
            "restricted": self.restricted
        }

        return master_branch_dict
