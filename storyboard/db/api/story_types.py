# Copyright (c) 2014 Mirantis Inc.
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

from storyboard.db.api import base as api_base
from storyboard.db import models


def story_type_get(story_type_id, session=None):
    return api_base.entity_get(models.StoryType, story_type_id, session)


def story_type_get_mutations(story_type_id_from, story_type_id_to):
    query = api_base.model_query(models.may_mutate_to)
    query = query.filter_by(story_type_id_from=story_type_id_from,
                            story_type_id_to=story_type_id_to)

    return query.first()
