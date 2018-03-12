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

from storyboard.migrate.launchpad.reader import LaunchpadReader
from storyboard.migrate.launchpad.writer import LaunchpadWriter


class LaunchpadLoader(object):
    def __init__(self, from_project, to_project, only_tags=None,
                 excluded_tags=None):
        """Create a new loader instance from launchpad.org
        """
        self.writer = LaunchpadWriter(to_project)
        self.reader = LaunchpadReader(from_project)
        self.only_tags = only_tags
        self.excluded_tags = excluded_tags

    def bug_matches_requested_tags(self, tags):
        """Check whether the set of tag matches the requirement:
           - the tag is in the set of the requested tags
             if the inclusion list is specified;
           - the tag is not in the set of the excluded tags
             if the inclusion list is specified.
        """
        if self.only_tags:
            return (tags.intersection(self.only_tags) == self.only_tags)
        if self.excluded_tags:
            return not tags.intersection(self.excluded_tags)
        return True

    def run(self):
        for lp_bug in self.reader:
            bug = lp_bug.bug

            tags_set = set()
            if hasattr(bug, 'tags') and bug.tags:
                tags_set = set(bug.tags)
            if not self.bug_matches_requested_tags(tags_set):
                print("WARNING: Skipping bug %s due to tag rules" %
                      (bug.self_link))
                continue

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

            links = [task.target_link for task in bug.bug_tasks]
            releases = ['kilo', 'liberty', 'mitaka', 'newton', 'ocata',
                        'pike', 'queens']
            branches = []

            #Strip ugliness off of links to bugs
            for branch in links:
                split_branch = branch.split('launchpad.net')
                url_parts = split_branch[1].split('/')
                branch_name = url_parts[-1].lower()
                project_name = url_parts[-2]

                if (branch_name in releases and
                   project_name == self.reader.project_name):
                    branches.append(branch_name)
                elif branch_name == self.reader.project_name:
                    branches.append('master')

            # Write the bug
            priority = map_lp_priority(lp_bug.importance)
            status = map_lp_status(lp_bug.status)
            self.writer.write_bug(bug=bug,
                                  owner=owner,
                                  assignee=assignee,
                                  priority=priority,
                                  status=status,
                                  tags=tags,
                                  branches=branches)


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

    if lp_status in ('Unknown', 'New', 'Confirmed', 'Triaged',
                     "Incomplete (with response)",
                     "Incomplete (without response)"):
        return 'todo'
    elif lp_status in ("Opinion", "Invalid", "Won't Fix", "Expired"):
        return 'invalid'
    elif lp_status == 'In Progress':
        return 'inprogress'
    elif lp_status in ('Fix Committed', 'Fix Released'):
        return 'merged'

    return 'invalid'
