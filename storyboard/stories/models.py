# Copyright 2011 Thierry Carrez <thierry@openstack.org>
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from django.contrib.auth.models import User
from django.db import models

from storyboard.projects.models import Milestone
from storyboard.projects.models import Project


class Story(models.Model):
    STORY_TYPES = (
        ('B', 'Bug'),
        ('F', 'Feature'),
    )
    STORY_PRIORITIES = (
        (4, 'Critical'),
        (3, 'High'),
        (2, 'Medium'),
        (1, 'Low'),
        (0, 'Undefined'),
    )
    creator = models.ForeignKey(User)
    title = models.CharField(max_length=100)
    description = models.TextField()
    story_type = models.CharField(max_length=1, choices=STORY_TYPES)
    priority = models.IntegerField(choices=STORY_PRIORITIES)

    def __unicode__(self):
        return str(self.id)


class Task(models.Model):
    TASK_STATUSES = (
        ('T', 'Todo'),
        ('R', 'In review'),
        ('L', 'Landed'),
    )
    story = models.ForeignKey(Story)
    title = models.CharField(max_length=100, blank=True)
    project = models.ForeignKey(Project)
    assignee = models.ForeignKey(User, blank=True, null=True)
    status = models.CharField(max_length=1, choices=TASK_STATUSES, default='T')
    milestone = models.ForeignKey(Milestone)

    def __unicode__(self):
        return "%s %s/%s" % (
            self.story.id, self.project.name, self.branch.short_name)


class Comment(models.Model):
    story = models.ForeignKey(Story)
    posted_date = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(User)
    action = models.CharField(max_length=150, blank=True)
    comment_type = models.CharField(max_length=20)
    content = models.TextField(blank=True)

    class Meta:
        ordering = ['posted_date']


class StoryTag(models.Model):
    story = models.ForeignKey(Story)
    name = models.CharField(max_length=20)
