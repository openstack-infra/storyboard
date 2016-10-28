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

import datetime
import pytz

from sqlalchemy.orm import subqueryload

from storyboard.common import exception as exc
from storyboard.db.api import base as api_base
from storyboard.db.api import story_tags
from storyboard.db.api import story_types
from storyboard.db.api import teams as teams_api
from storyboard.db.api import users as users_api
from storyboard.db import models
from storyboard.openstack.common.gettextutils import _  # noqa


def story_get_simple(story_id, session=None, current_user=None,
                     no_permissions=False):
    """Return a story with the given ID.

    The `no_permissions` parameter should only ever be used in situations
    where the permissions have already been checked. For example, when
    updating the "updated_at" field when comments are made on stories.

    :param story_id: ID of the story to return.
    :param session: DB session to use.
    :param current_user: The ID of the user making the request.
    :param no_permissions: Skip filtering stories by permission.
    :return: The story being searched for, or None if nothing found.

    """
    query = api_base.model_query(models.Story, session) \
        .options(subqueryload(models.Story.tags)) \
        .filter_by(id=story_id)

    if not no_permissions:
        # Filter out stories that the current user can't see
        query = api_base.filter_private_stories(query, current_user)

    return query.first()


def story_get(story_id, session=None, current_user=None):
    query = api_base.model_query(models.StorySummary, session)
    query = query.options(subqueryload(models.StorySummary.tags))\
        .filter_by(id=story_id)

    # Filter out stories that the current user can't see
    query = api_base.filter_private_stories(query, current_user,
                                            story_model=models.StorySummary)

    return query.first()


def story_get_all(title=None, description=None, status=None, assignee_id=None,
                  creator_id=None, project_group_id=None, project_id=None,
                  subscriber_id=None, tags=None, updated_since=None,
                  marker=None, offset=None,
                  limit=None, tags_filter_type="all", sort_field='id',
                  sort_dir='asc', current_user=None):
    # Sanity checks, in case someone accidentally explicitly passes in 'None'
    if not sort_field:
        sort_field = 'id'
    if not sort_dir:
        sort_dir = 'asc'

    if not isinstance(status, list) and status is not None:
        status = [status]

    # Build the query.
    subquery = _story_build_query(title=title,
                                  description=description,
                                  assignee_id=assignee_id,
                                  creator_id=creator_id,
                                  project_group_id=project_group_id,
                                  project_id=project_id,
                                  tags=tags,
                                  updated_since=updated_since,
                                  tags_filter_type=tags_filter_type,
                                  current_user=current_user)

    # Filter by subscriber ID
    if subscriber_id is not None:
        subs = api_base.model_query(models.Subscription)
        subs = api_base.apply_query_filters(query=subs,
                                            model=models.Subscription,
                                            target_type='story',
                                            user_id=subscriber_id)
        subs = subs.subquery()
        subquery = subquery.join(subs, subs.c.target_id == models.Story.id)

    # Turn the whole shebang into a subquery.
    subquery = subquery.subquery('filtered_stories')

    # Return the story summary.
    query = api_base.model_query(models.StorySummary)\
        .options(subqueryload(models.StorySummary.tags))
    query = query.join(subquery,
                       models.StorySummary.id == subquery.c.stories_id)

    if status:
        query = query.filter(models.StorySummary.status.in_(status))

    # paginate the query
    query = api_base.paginate_query(query=query,
                                    model=models.StorySummary,
                                    limit=limit,
                                    sort_key=sort_field,
                                    marker=marker,
                                    offset=offset,
                                    sort_dir=sort_dir)

    raw_stories = query.all()
    return raw_stories


def story_get_count(title=None, description=None, status=None,
                    assignee_id=None, creator_id=None,
                    project_group_id=None, project_id=None,
                    subscriber_id=None, tags=None, updated_since=None,
                    tags_filter_type="all", current_user=None):
    query = _story_build_query(title=title,
                               description=description,
                               assignee_id=assignee_id,
                               creator_id=creator_id,
                               project_group_id=project_group_id,
                               project_id=project_id,
                               updated_since=updated_since,
                               tags=tags,
                               tags_filter_type=tags_filter_type,
                               current_user=current_user)

    # Filter by subscriber ID
    if subscriber_id is not None:
        subs = api_base.model_query(models.Subscription)
        subs = api_base.apply_query_filters(query=subs,
                                            model=models.Subscription,
                                            target_type='story',
                                            user_id=subscriber_id)
        subs = subs.subquery()
        query = query.join(subs, subs.c.target_id == models.Story.id)

    # If we're also asking for status, we have to attach storysummary here,
    # since story status is derived.
    if status:
        query = query.subquery()
        summary_query = api_base.model_query(models.StorySummary)
        summary_query = summary_query \
            .join(query, models.StorySummary.id == query.c.stories_id)
        query = summary_query.filter(models.StorySummary.status.in_(status))

    return query.count()


def _story_build_query(title=None, description=None, assignee_id=None,
                       creator_id=None, project_group_id=None,
                       project_id=None, updated_since=None, tags=None,
                       tags_filter_type='all', current_user=None):
    # First build a standard story query.
    query = api_base.model_query(models.Story.id).distinct()

    # Apply basic filters
    query = api_base.apply_query_filters(query=query,
                                         model=models.Story,
                                         title=title,
                                         description=description,
                                         creator_id=creator_id)
    if updated_since:
        query = query.filter(models.Story.updated_at > updated_since)

    # Filter out stories that the current user can't see
    query = api_base.filter_private_stories(query, current_user)

    # Filtering by tags
    if tags:
        if tags_filter_type == 'all':
            for tag in tags:
                query = query.filter(models.Story.tags.any(name=tag))
        elif tags_filter_type == 'any':
            query = query.filter(models.Story.tags.any
                                 (models.StoryTag.name.in_(tags)))
        else:
            raise exc.NotFound("Tags filter not found.")

    # Are we filtering by project group?
    if project_group_id:
        query = query.join(
            (models.Task, models.Task.story_id == models.Story.id))
        query = query.join(models.Project,
                           models.project_group_mapping,
                           models.ProjectGroup)
        query = query.filter(models.ProjectGroup.id == project_group_id)

    # Are we filtering by task?
    if assignee_id or project_id:
        if not project_group_id:  # We may already have joined this table
            query = query.join(
                (models.Task, models.Task.story_id == models.Story.id))
        if assignee_id:
            query = query.filter(models.Task.assignee_id == assignee_id)
        if project_id:
            query = query.filter(models.Task.project_id == project_id)

    return query.distinct()


def story_create(values):
    return api_base.entity_create(models.Story, values)


def story_update(story_id, values, current_user=None):
    api_base.entity_update(models.Story, story_id, values)
    return story_get(story_id, current_user=current_user)


def story_update_updated_at(story_id):
    session = api_base.get_session()

    with session.begin(subtransactions=True):
        story = story_get_simple(story_id, session=session,
                                 no_permissions=True)
        if not story:
            raise exc.NotFound(_("%(name)s %(id)s not found") %
                               {'name': "Story", 'id': story_id})
        story.updated_at = datetime.datetime.now(tz=pytz.utc)
        session.add(story)
    session.expunge(story)


def story_add_tag(story_id, tag_name, current_user=None):
    session = api_base.get_session()

    with session.begin(subtransactions=True):

        # Get a tag or create a new one
        tag = story_tags.tag_get_by_name(tag_name, session=session)
        if not tag:
            tag = story_tags.tag_create({"name": tag_name})

        story = story_get_simple(
            story_id, session=session, current_user=current_user)
        if not story:
            raise exc.NotFound(_("%(name)s %(id)s not found") %
                               {'name': "Story", 'id': story_id})

        if tag_name in [t.name for t in story.tags]:
            raise exc.DBDuplicateEntry(
                _("The Story %(id)d already has a tag %(tag)s") %
                {'id': story_id, 'tag': tag_name})

        story.tags.append(tag)
        story.updated_at = datetime.datetime.now(tz=pytz.utc)
        session.add(story)
    session.expunge(story)


def story_remove_tag(story_id, tag_name, current_user=None):
    session = api_base.get_session()

    with session.begin(subtransactions=True):

        story = story_get_simple(
            story_id, session=session, current_user=current_user)
        if not story:
            raise exc.NotFound(_("%(name)s %(id)s not found") %
                               {'name': "Story", 'id': story_id})

        if tag_name not in [t.name for t in story.tags]:
            raise exc.NotFound(_("The Story %(story_id)d has "
                                 "no tag %(tag)s") %
                               {'story_id': story_id, 'tag': tag_name})

        tag = [t for t in story.tags if t.name == tag_name][0]
        story.tags.remove(tag)
        story.updated_at = datetime.datetime.now(tz=pytz.utc)
        session.add(story)
    session.expunge(story)


def story_delete(story_id, current_user=None):
    story = story_get(story_id, current_user=current_user)

    if story:
        api_base.entity_hard_delete(models.Story, story_id)


def story_check_story_type_id(story_dict):
    if "story_type_id" in story_dict and not story_dict["story_type_id"]:
        del story_dict["story_type_id"]


def story_can_create_story(story_type_id):
    if not story_type_id:
        return True

    story_type = story_types.story_type_get(story_type_id)

    if not story_type:
        raise exc.NotFound("Story type %s not found." % story_type_id)

    if not story_type.visible:
        return False

    return True


def story_can_mutate(story, new_story_type_id):
    if not new_story_type_id:
        return True

    if story.story_type_id == new_story_type_id:
        return True

    old_story_type = story_types.story_type_get(story.story_type_id)
    new_story_type = story_types.story_type_get(new_story_type_id)

    if not new_story_type:
        raise exc.NotFound(_("Story type %s not found.") % new_story_type_id)

    if not old_story_type.private and new_story_type.private:
        return False

    mutation = story_types.story_type_get_mutations(story.story_type_id,
                                                    new_story_type_id)

    if not mutation:
        return False

    if not new_story_type.restricted:
        return True

    query = api_base.model_query(models.Task)
    query = query.filter_by(story_id=story.id)
    tasks = query.all()
    branch_ids = set()

    for task in tasks:
        if task.branch_id:
            branch_ids.add(task.branch_id)

    branch_ids = list(branch_ids)

    query = api_base.model_query(models.Branch)
    branch = query.filter(models.Branch.id.in_(branch_ids),
                          models.Branch.restricted.__eq__(1)).first()

    if not branch:
        return True

    return False


def create_permission(story, users, teams, session=None):
    story = api_base.model_query(models.Story, session) \
        .options(subqueryload(models.Story.tags)) \
        .filter_by(id=story.id).first()
    permission_dict = {
        'name': 'view_story_%d' % story.id,
        'codename': 'view_story'
    }
    permission = api_base.entity_create(models.Permission, permission_dict)
    story.permissions.append(permission)
    if users is not None:
        for user in users:
            user = users_api.user_get(user.id)
            user.permissions.append(permission)
    if teams is not None:
        for team in teams:
            team = teams_api.team_get(team.id)
            team.permissions.append(permission)
    return permission


def update_permission(story, users, teams, session=None):
    story = api_base.model_query(models.Story, session) \
        .options(subqueryload(models.Story.tags)) \
        .filter_by(id=story.id).first()
    if not story.permissions:
        raise exc.NotFound(_("Permissions for story %d not found.")
                           % story.id)
    permission = story.permissions[0]
    permission_dict = {
        'name': permission.name,
        'codename': permission.codename
    }
    if users is not None:
        permission_dict['users'] = [users_api.user_get(user.id)
                                    for user in users]
    if teams is not None:
        permission_dict['teams'] = [teams_api.team_get(team.id)
                                    for team in teams]

    return api_base.entity_update(models.Permission,
                                  permission.id,
                                  permission_dict)
