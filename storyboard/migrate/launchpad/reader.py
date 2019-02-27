# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from launchpadlib import launchpad


class LaunchpadReader(object):
    """A generator that allows us to easily loop over launchpad bugs in any
    given project.
    """

    def __init__(self, project_name):
        self.lp = launchpad.Launchpad.login_anonymously('storyboard',
                                                        'production')
        self.project_name = project_name
        self.project = self.lp.projects[project_name]
        self.tasks = self.project.searchTasks(
            status=["New", "Incomplete (with response)",
                    "Incomplete (without response)", "Invalid", "Won't Fix",
                    "Confirmed", "Triaged", "Opinion", "Expired",
                    "In Progress", "Fix Committed", "Fix Released"])
        self.task_iterator = self.tasks.__iter__()

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self):
        return next(self.task_iterator)
