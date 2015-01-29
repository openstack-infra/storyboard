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


class NameType(types.StringType):
    """This type should be applied to the name fields. Currently this type
    should be applied to Projects and Project Groups.

    This type allows alphanumeric characters with . - and / separators inside
    the name. The name should be at least 3 symbols long.

    """

    _name_regex = r'^[a-zA-Z0-9]+([_\-\./]?[a-zA-Z0-9]+)*$'

    def __init__(self):
        super(NameType, self).__init__(min_length=3, pattern=self._name_regex)
