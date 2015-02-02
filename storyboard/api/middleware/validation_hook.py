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

import jsonschema

from pecan import abort
from pecan import hooks

import storyboard.common.hook_priorities as priority


class ValidationHook(hooks.PecanHook):

    priority = priority.VALIDATION

    def validate(self, json_body, schema):
        try:
            jsonschema.validate(json_body, schema)
        except jsonschema.ValidationError as invalid:
            error_field = '.'.join(invalid.path)

            abort(400, json_body={"message": invalid.message,
                                  "field": error_field})

    def before(self, state):
        request = state.request
        method = request.method

        if method == 'POST':
            if hasattr(state.controller.__self__, 'validation_post_schema'):
                schema = state.controller.__self__.validation_post_schema
                json_body = request.json
                self.validate(json_body, schema)
        elif method == 'PUT':
            if hasattr(state.controller.__self__, 'validation_put_schema'):
                schema = state.controller.__self__.validation_put_schema
                json_body = request.json
                self.validate(json_body, schema)
