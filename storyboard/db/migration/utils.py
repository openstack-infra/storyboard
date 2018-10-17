# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#

import functools

from alembic import op


def not_sqlite(f):
    "Decorator to skip migrations for sqlite databases."
    @functools.wraps(f)
    def upgrade(active_plugins=None, options=None):
        dialect = op.get_bind().engine.dialect
        if dialect.name == 'sqlite':
            return
        return f(active_plugins, options)
    return upgrade
