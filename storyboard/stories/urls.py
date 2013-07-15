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

from django.conf.urls.defaults import *


urlpatterns = patterns('storyboard.stories.views',
    (r'^$', 'dashboard'),
    (r'^(\d+)$', 'view'),
    (r'^(\d+)/addtask$', 'add_task'),
    (r'^new$', 'add_story'),
    (r'^(\d+)/edit$', 'edit_story'),
    (r'^(\d+)/comment$', 'comment'),
    (r'^(\d+)/priority$', 'set_priority'),
    (r'^task/(\d+)$', 'edit_task'),
    (r'^task/(\d+)/delete$', 'delete_task'),
)
