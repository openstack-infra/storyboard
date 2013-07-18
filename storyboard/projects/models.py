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

from django.db import models


class Project(models.Model):
    name = models.CharField(max_length=50, primary_key=True)
    title = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name


class Branch(models.Model):
    BRANCH_STATUS = (
        ('M', 'master'),
        ('R', 'release'),
        ('S', 'stable'),
        ('U', 'unsupported'))
    name = models.CharField(max_length=50)
    short_name = models.CharField(max_length=20)
    status = models.CharField(max_length=1, choices=BRANCH_STATUS)
    release_date = models.DateTimeField()

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['release_date']


class Milestone(models.Model):
    name = models.CharField(max_length=50)
    branch = models.ForeignKey(Branch)
    released = models.BooleanField(default=False)
    undefined = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['name']
