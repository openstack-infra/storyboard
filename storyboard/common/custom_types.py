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

from wsme import types


class Name(types.StringType):

    # alpha-numeric, all kind of brackets, minus, slash, underscore and space
    # at least 3 alpha-numeric symbols
    _name_regex = r'^[a-zA-Z0-9\-_\[\]\(\)\{\}/\s]*' \
                  r'[a-zA-Z0-9]{3,}' \
                  r'[a-zA-Z0-9\-_\[\]\(\)\{\}/\s]*$'

    def __init__(self):
        super(Name, self).__init__(pattern=self._name_regex)
