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

import shelve
import tempfile

from storyboard.migrate.launchpad.reader import LaunchpadReader
from storyboard.migrate.launchpad.writer import LaunchpadWriter


class LaunchpadLoader(object):
    def __init__(self, from_project, to_project):
        """Create a new loader instance from launchpad.org
        """
        tmp_dir = tempfile.gettempdir()
        self.cache = shelve.open("%s/launchpad_migrate.db" % (tmp_dir))
        self.writer = LaunchpadWriter(to_project)
        self.reader = LaunchpadReader(from_project)

    def run(self):
        for lp_bug in self.reader:
            bug = lp_bug.bug
            cache_key = str(unicode(bug.self_link))

            if cache_key not in self.cache:
                # Preload the tags.
                tags = self.writer.write_tags(bug)

                # Preload the story owner.
                owner = self.writer.write_user(bug.owner)

                # Preload the story's assignee (stored on lp_bug, not bug).
                if hasattr(lp_bug, 'assignee') and lp_bug.assignee:
                    assignee = self.writer.write_user(lp_bug.assignee)
                else:
                    assignee = None

                # Preload the story discussion participants.
                for message in bug.messages:
                    self.writer.write_user(message.owner)

                # Write the bug.
                priority = map_lp_priority(lp_bug.importance)
                status = map_lp_status(lp_bug.status)
                story = self.writer.write_bug(bug=bug,
                                              owner=owner,
                                              assignee=assignee,
                                              priority=priority,
                                              status=status,
                                              tags=tags)

                # Cache things.
                self.cache[cache_key] = story.id


def map_lp_priority(lp_priority):
    """Map a launchpad priority to a storyboard priority.
    """
    if lp_priority in ('Unknown', 'Undecided', 'Medium'):
        return 'medium'
    elif lp_priority in ('Critical', 'High'):
        return 'high'
    return 'low'


def map_lp_status(lp_status):
    """Map a launchpad status to a storyboard priority.

    """
    # ('todo', 'inprogress', 'invalid', 'review', 'merged')

    if lp_status in ('Unknown', 'New', 'Confirmed', 'Triaged'):
        return 'todo'
    elif lp_status in (
            'Incomplete', 'Opinion', 'Invalid', "Won't Fix",
            'Expired'):
        return 'invalid'
    elif lp_status == 'In Progress':
        return 'inprogress'
    elif lp_status in ('Fix Committed', 'Fix Released'):
        return 'merged'

    return 'invalid'
