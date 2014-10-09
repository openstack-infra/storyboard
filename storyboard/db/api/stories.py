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

from oslo.db.sqlalchemy.utils import InvalidSortKey
from sqlalchemy.orm import subqueryload
from wsme.exc import ClientSideError

from storyboard.common import exception as exc
from storyboard.db.api import base as api_base
from storyboard.db.api import tags
from storyboard.db import models


def story_get_simple(story_id, session=None):
    return api_base.model_query(models.Story, session)\
        .options(subqueryload(models.Story.tags))\
        .filter_by(id=story_id).first()


def story_get(story_id, session=None):
    story_summary_query = api_base.model_query(models.StorySummary, session)
    story_summary = story_summary_query.filter_by(id=story_id).first()

    simple = story_get_simple(story_id)
    if simple and story_summary:
        story_summary.tags = simple.tags
        return story_summary
    else:
        return simple


def story_get_all(marker=None, limit=None, story_filters=None,
                  task_filters=None, sort_field='id', sort_dir='asc'):
    query = _story_build_query(story_filters=story_filters,
                               task_filters=task_filters)

    # Sanity checks, in case someone accidentally explicitly passes in 'None'
    if not sort_field:
        sort_field = 'id'
    if not sort_dir:
        sort_dir = 'asc'

    # paginate the query
    try:
        query = api_base.paginate_query(query=query,
                                        model=models.StorySummary,
                                        limit=limit,
                                        sort_keys=[sort_field],
                                        marker=marker,
                                        sort_dir=sort_dir)
    except InvalidSortKey:
        raise ClientSideError("Invalid sort_field [%s]" % (sort_field,),
                              status_code=400)
    except ValueError as ve:
        raise ClientSideError("%s" % (ve,), status_code=400)

    return query.all()


def story_get_count(story_filters=None, task_filters=None):
    query = _story_build_query(story_filters=story_filters,
                               task_filters=task_filters)
    return query.count()


def _story_build_query(story_filters=None, task_filters=None):
    # Input sanity checks
    if story_filters:
        story_filters = dict((k, v) for k, v in story_filters.iteritems() if v)
    if task_filters:
        task_filters = dict((k, v) for k, v in task_filters.iteritems() if v)

    # Build the main story query
    query = api_base.model_query(models.StorySummary)
    query = api_base.apply_query_filters(query=query,
                                         model=models.StorySummary,
                                         **story_filters)

    # Do we have task parameter queries we need to deal with?
    if task_filters and len(task_filters) > 0:
        subquery = api_base.model_query(models.Task.story_id) \
            .filter_by(**task_filters) \
            .distinct(True) \
            .subquery('project_tasks')

        query = query.join(subquery,
                           models.StorySummary.id == subquery.c.story_id)

    return query


def story_create(values):
    return api_base.entity_create(models.Story, values)


def story_update(story_id, values):
    return api_base.entity_update(models.Story, story_id, values)


def story_add_tag(story_id, tag_name):
    session = api_base.get_session()

    with session.begin():

        # Get a tag or create a new one
        tag = tags.tag_get_by_name(tag_name, session=session)
        if not tag:
            tag = tags.tag_create({"name": tag_name})

        story = story_get_simple(story_id, session=session)
        if not story:
            raise exc.NotFound("%s %s not found" % ("Story", story_id))

        if tag_name in [t.name for t in story.tags]:
            raise ClientSideError("The Story %d already has a tag %s" %
                                  (story_id, tag_name))

        story.tags.append(tag)
        session.add(story)


def story_remove_tag(story_id, tag_name):
    session = api_base.get_session()

    with session.begin():

        story = story_get_simple(story_id, session=session)
        if not story:
            raise exc.NotFound("%s %s not found" % ("Story", story_id))

        if tag_name not in [t.name for t in story.tags]:
            raise ClientSideError("The Story %d has no tag %s" %
                                  (story_id, tag_name))

        tag = [t for t in story.tags if t.name == tag_name][0]
        story.tags.remove(tag)
        session.add(story)


def story_get_by_tags(*tags):
    query = api_base.model_query(models.Story)

    for tag in tags:
        query = query.filter(models.Story.tags.any(name=tag))

    return query.all()


def story_delete(story_id):
    story = story_get(story_id)

    if story:
        api_base.entity_hard_delete(models.Story, story_id)
