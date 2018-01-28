# Copyright (c) 2018 IBM Corp.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from oslo_config import cfg
from oslo_utils import importutils

from storyboard.notifications import conf

CONF = cfg.CONF
CONF.register_opts(conf.OPTS, 'notifications')


def publish(resource, author_id=None, method=None, url=None, path=None,
            query_string=None, status=None, resource_id=None,
            sub_resource=None, sub_resource_id=None, resource_before=None,
            resource_after=None):

    publisher_module = importutils.import_module(
        'storyboard.notifications.' + CONF.notifications.driver + '.publisher')
    publisher_module.publish(resource, author_id=author_id, method=method,
                             url=url, path=path, query_string=query_string,
                             status=status, resource_id=resource_id,
                             sub_resource=sub_resource,
                             sub_resource_id=sub_resource_id,
                             resource_before=resource_before,
                             resource_after=resource_after)
