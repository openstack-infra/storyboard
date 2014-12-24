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

import imp
import os

from alembic.script import ScriptDirectory
import six
import testtools

from storyboard.db.migration.cli import get_alembic_config


class UniqueRevisionsTestCase(testtools.TestCase):

    def test_revisions(self):
        alembic_config = get_alembic_config()
        directory = ScriptDirectory.from_config(alembic_config)
        versions_path = directory.versions
        files = os.listdir(versions_path)

        revisions = set([])
        down_revisions = set([])

        for f in files:
            if not f.endswith(".py"):
                # Skipping README and all .pyc files if there are any.
                continue

            module_path = os.path.join(versions_path, f)
            module = imp.load_source('module', six.text_type(module_path))
            revision_id = module.revision

            self.assertFalse(revision_id in revisions,
                             "Found two revisions with id %s" % revision_id)
            revisions.add(revision_id)

            down_revision_id = module.revision

            self.assertFalse(down_revision_id in down_revisions,
                             "Found two revisions with down_revision_id %s"
                             % revision_id)
            down_revisions.add(down_revision_id)
