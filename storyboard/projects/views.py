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

from collections import OrderedDict

from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from storyboard.projects.models import Project
from storyboard.projects import utils
from storyboard.stories.models import Task


def default_list(request):
    return render(request, "projects.list.html", {
        'projects': Project.objects.all(),
    })


def dashboard(request, projectname, group=False):
    ref, projects = utils.retrieve_projects(projectname, group)
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
    page_type = "featuretasks"

    ref, projects = utils.retrieve_projects(projectname, group)
    bugcount = Task.objects.filter(project__in=projects,
                                   story__is_bug=True,
                                   story__priority=0).count()
    featuretasks = Task.objects.filter(project__in=projects,
                                       story__is_bug=False,
                                       status__in=['T', 'R'])
    featuretasks = utils.order_results(request, page_type, featuretasks)

    p_size, p_count, p_number = utils.get_pagination(request,
                                                     len(featuretasks))
    if p_size != -1:
        featuretasks = featuretasks[p_number * p_size: (p_number + 1) * p_size]

    arrow_object = utils.build_order_arrows_object(request, page_type)

    return render(request, "projects.list_tasks.html", {
        'title': "Active feature tasks",
        'page_type': page_type,
        'ref': ref,
        'is_group': group,
        'name': projectname,
        'bugtriagecount': bugcount,
        'tasks': featuretasks,
        'page_count': p_count,
        'page_number': p_number,
        'page_size': p_size,
        'arrow_object': arrow_object,
        'is_bug': False
    })


def list_bugtasks(request, projectname, group=False):
    page_type = "bugtasks"

    ref, projects = utils.retrieve_projects(projectname, group)
    bugcount = Task.objects.filter(project__in=projects,
                                   story__is_bug=True,
                                   story__priority=0).count()
    bugtasks = Task.objects.filter(project__in=projects,
                                   story__is_bug=True,
                                   status__in=['T', 'R'])
    bugtasks = utils.order_results(request, page_type, bugtasks)

    p_size, p_count, p_number = utils.get_pagination(request, len(bugtasks))
    if p_size != -1:
        bugtasks = bugtasks[p_number * p_size: (p_number + 1) * p_size]

    arrow_object = utils.build_order_arrows_object(request, page_type)

    return render(request, "projects.list_tasks.html", {
        'title': "Active bug tasks",
        'page_type': page_type,
        'ref': ref,
        'is_group': group,
        'bugtriagecount': bugcount,
        'tasks': bugtasks,
        'page_count': p_count,
        'page_number': p_number,
        'page_size': p_size,
        'arrow_object': arrow_object,
        'is_bug': True,
    })


def list_bugtriage(request, projectname, group=False):
    page_type = "bugtriage"

    ref, projects = utils.retrieve_projects(projectname, group)
    tasks = Task.objects.filter(project__in=projects,
                                story__is_bug=True,
                                story__priority=0)
    tasks = utils.order_results(request, page_type, tasks)
    bugcount = tasks.count()

    p_size, p_count, p_number = utils.get_pagination(request, len(tasks))
    if p_size != -1:
        tasks = tasks[p_number * p_size: (p_number + 1) * p_size]

    arrow_object = utils.build_order_arrows_object(request, page_type)

    return render(request, "projects.list_tasks.html", {
        'title': "Bugs needing triage",
        'page_type': page_type,
        'ref': ref,
        'is_group': group,
        'bugtriagecount': bugcount,
        'tasks': tasks,
        'page_count': p_count,
        'page_number': p_number,
        'page_size': p_size,
        'arrow_object': arrow_object,
        'is_bug': True,
    })


@require_POST
def set_order(request):
    order_dict = request.session.get("order_dict", dict())
    page_type = request.POST.get("page_type")
    order_field = request.POST.get("order_field")

    # multi_filed ordering will be implemented later with search requests
    multi_field = request.POST.get("is_multi_field")

    if not order_field:
        raise RuntimeError("order_field is not set")

    if page_type not in order_dict:
        order_dict[page_type] = utils.build_default_order_dict()

    order_type = order_dict[page_type].get(order_field)

    if not multi_field:
        order_dict[page_type] = OrderedDict()

    if not order_type:
        order_type = "desc"
    else:
        order_type = "asc" if order_type == "desc" else "desc"

    order_dict[page_type][order_field] = order_type

    # Save dict to session if it was recently created
    request.session["order_dict"] = order_dict

    return HttpResponse(status=202)
