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

from django.shortcuts import render

from storyboard.projects.models import Project
from storyboard.projects.utils import retrieve_projects
from storyboard.stories.models import Task


def default_list(request):
    return render(request, "projects.list.html", {
        'projects': Project.objects.all(),
    })


def dashboard(request, projectname, group=False):
    ref, projects = retrieve_projects(projectname, group)
    bugcount = Task.objects.filter(project__in=projects,
                                   story__is_bug=True,
                                   story__priority=0).count()
    if group:
        return render(request, "projects.group.html", {
            'ref': ref,
            'is_group': group,
            'bugtriagecount': bugcount,
        })
    return render(request, "projects.dashboard.html", {
        'ref': ref,
        'is_group': group,
        'bugtriagecount': bugcount,
    })


def list_featuretasks(request, projectname, group=False):
    ref, projects = retrieve_projects(projectname, group)
    bugcount = Task.objects.filter(project__in=projects,
                                   story__is_bug=True,
                                   story__priority=0).count()
    featuretasks = Task.objects.filter(project__in=projects,
                                   story__is_bug=False,
                                   status__in=['T', 'R'])
    return render(request, "projects.list_tasks.html", {
        'title': "Active feature tasks",
        'ref': ref,
        'is_group': group,
        'name': projectname,
        'bugtriagecount': bugcount,
        'tasks': featuretasks,
        'is_bug': False,
    })


def list_bugtasks(request, projectname, group=False):
    ref, projects = retrieve_projects(projectname, group)
    bugcount = Task.objects.filter(project__in=projects,
                                   story__is_bug=True,
                                   story__priority=0).count()
    bugtasks = Task.objects.filter(project__in=projects,
                                   story__is_bug=True,
                                   status__in=['T', 'R'])
    return render(request, "projects.list_tasks.html", {
        'title': "Active bug tasks",
        'ref': ref,
        'is_group': group,
        'bugtriagecount': bugcount,
        'tasks': bugtasks,
        'is_bug': True,
    })


def list_bugtriage(request, projectname, group=False):
    ref, projects = retrieve_projects(projectname, group)
    tasks = Task.objects.filter(project__in=projects,
                                story__is_bug=True,
                                story__priority=0)
    bugcount = tasks.count()
    return render(request, "projects.list_tasks.html", {
        'title': "Bugs needing triage",
        'ref': ref,
        'is_group': group,
        'bugtriagecount': bugcount,
        'tasks': tasks,
        'is_bug': True,
    })
