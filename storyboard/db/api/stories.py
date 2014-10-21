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
    return api_base.model_query(models.Story, session) \
        .options(subqueryload(models.Story.tags)) \
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


def story_get_all(title=None, description=None, status=None, assignee_id=None,
                  project_group_id=None, project_id=None, marker=None,
                  limit=None, sort_field='id', sort_dir='asc'):
    # Sanity checks, in case someone accidentally explicitly passes in 'None'
    if not sort_field:
        sort_field = 'id'
    if not sort_dir:
        sort_dir = 'asc'

    # Build the query.
    subquery = _story_build_query(title=title,
                                  description=description,
                                  assignee_id=assignee_id,
                                  project_group_id=project_group_id,
                                  project_id=project_id)

    # Turn the whole shebang into a subquery.
    subquery = subquery.subquery('filtered_stories')

    # Return the story summary.
    query = api_base.model_query(models.StorySummary)
    query = query.join(subquery,
                       models.StorySummary.id == subquery.c.id)

    if status:
        query = query.filter(models.StorySummary.status.in_(status))

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


def story_get_count(title=None, description=None, status=None,
                    assignee_id=None, project_group_id=None, project_id=None):
    query = _story_build_query(title=title,
                               description=description,
                               assignee_id=assignee_id,
                               project_group_id=project_group_id,
                               project_id=project_id)

    # If we're also asking for status, we have to attach storysummary here,
    # since story status is derived.
    if status:
        query = query.subquery()
        summary_query = api_base.model_query(models.StorySummary)
        summary_query = summary_query \
            .join(query, models.StorySummary.id == query.c.id)
        query = summary_query.filter(models.StorySummary.status.in_(status))

    return query.count()


def _story_build_query(title=None, description=None, assignee_id=None,
                       project_group_id=None, project_id=None):
    # First build a standard story query.
    query = api_base.model_query(models.Story.id).distinct()
    query = api_base.apply_query_filters(query=query,
                                         model=models.Story,
                                         title=title,
                                         description=description)

    # Are we filtering by project group?
    if project_group_id:
        query = query.join(models.Task,
                           models.Project,
                           models.project_group_mapping)
        query = query.filter(project_group_id == project_group_id)

    # Are we filtering by task?
    if assignee_id or project_id:
        if not project_group_id:  # We may already have joined this table
            query = query.join(models.Task)
        if assignee_id:
            query = query.filter(models.Task.assignee_id == assignee_id)
        if project_id:
            query = query.filter(models.Task.project_id == project_id)

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
