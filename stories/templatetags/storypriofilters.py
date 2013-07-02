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

from django import template

register = template.Library()

badges = ['', ' badge-info', ' badge-success', ' badge-warning',
          ' badge-important']
buttons = ['', ' btn-info', ' btn-success', ' btn-warning', ' btn-danger']

@register.filter(name='priobadge')
def priobadge(value):
    if value < 5:
        return badges[value]
    else:
        return badges[4]

@register.filter(name='priobutton')
def priobutton(value):
    if value < 5:
        return buttons[value]
    else:
        return buttons[4]
