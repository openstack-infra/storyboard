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

import copy
from pecan import hooks

from storyboard.db import models


class ServerOwnedFieldsHook(hooks.PecanHook):
    def before(self, state):
        request = state.request
        method = request.method

        if method == 'PUT' or method == 'POST':
            json_body = copy.deepcopy(request.json)

            for item in models.SERVER_OWNED_FIELDS:
                if item in json_body:
                    del json_body[item]

            request.json = json_body
