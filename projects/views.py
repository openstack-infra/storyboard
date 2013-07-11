# Copyright 2013 Thierry Carrez <thierry@openstack.org>
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

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.auth import logout
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render

from projects.models import Project
from stories.models import Task

def default_list(request):
    return render(request, "projects.list.html", {
        'projects': Project.objects.all(),
        })

def dashboard(request, projectname):
    return render(request, "projects.dashboard.html", {
        'project': Project.objects.get(name=projectname),
        })

def list_bugtasks(request, projectname):
    project = Project.objects.get(name=projectname)
    return render(request, "projects.list_tasks.html", {
        'project': project,
        'tasks': Task.objects.filter(project=project),
        })
