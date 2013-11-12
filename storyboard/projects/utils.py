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
import six

from storyboard.projects.models import Project
from storyboard.projects.models import ProjectGroup


def retrieve_projects(name, group):
    if group:
        ref = ProjectGroup.objects.get(name=name)
        return ref, ref.members.all()
    else:
        ref = Project.objects.get(name=name)
        return ref, [ref]


def order_results(request, page_type, tasks):
    order_dict = request.session.get("order_dict")

    if not order_dict:
        order_dict = dict()
        request.session["order_dict"] = order_dict

    if page_type not in order_dict:
        order_dict[page_type] = build_default_order_dict()

    order_list = []

    for key, val in six.iteritems(order_dict[page_type]):
        order_param = key
        if val == "desc":
            order_param = "-%s" % order_param

        order_list.append(order_param)

    return tasks.order_by(*order_list)


def build_order_arrows_object(request, page_type):
    order_dict = request.session.get("order_dict")

    if not order_dict:
        return {}

    page_order_fields = order_dict.get(page_type)

    if not page_order_fields:
        return {}

    arrows_object = {}

    for field, order in six.iteritems(page_order_fields):
        arrows_object[field] = "up" if order == "asc" else "down"

    return arrows_object


def get_pagination(request, total_count):
    page_size = int(request.GET.get("page_size", 15))
    page_number = int(request.GET.get("page_number", 0))

    if page_number < -1:
        raise RuntimeError("Invalid page number")
    page_count = total_count / page_size
    if total_count % page_size > 0:
        page_count += 1

    return page_size, page_count, page_number


def build_default_order_dict():
    _dict = OrderedDict()
    _dict["story__priority"] = "desc"

    return _dict
