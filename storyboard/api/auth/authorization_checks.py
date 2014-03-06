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

from pecan import request

from storyboard.api.auth.oauth_validator import TOKEN_STORAGE


def guest():
    return True


def authenticated():

    result = False
    if request.authorization and len(request.authorization) == 2:
        token = request.authorization[1]
        if token and TOKEN_STORAGE.check_access_token(token):
            result = True

    return result
