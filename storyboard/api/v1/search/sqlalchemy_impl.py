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

from sqlalchemy.orm import subqueryload
from sqlalchemy_fulltext import FullTextSearch
import sqlalchemy_fulltext.modes as FullTextMode

from storyboard.api.v1.search import search_engine
from storyboard.db.api import base as api_base
from storyboard.db.api import stories as stories_api
from storyboard.db.api import tasks as tasks_api
from storyboard.db import models


class SqlAlchemySearchImpl(search_engine.SearchEngine):
    def _build_fulltext_search(self, model_cls, query, q):
        query = query.filter(FullTextSearch(q, model_cls,
                                            mode=FullTextMode.BOOLEAN))

        return query

    def _apply_pagination(self, model_cls, query, marker=None,
                          offset=None, limit=None, sort_field='id',
                          sort_dir='asc'):
        if not sort_field:
            sort_field = 'id'
        if not sort_dir:
            sort_dir = 'asc'

        marker_entity = None
        if marker:
            marker_entity = api_base.entity_get(model_cls, marker, True)

        return api_base.paginate_query(query=query,
                                       model=model_cls,
                                       limit=limit,
                                       sort_key=sort_field,
                                       marker=marker_entity,
                                       offset=offset,
                                       sort_dir=sort_dir)

    def projects_query(self, q, sort_dir=None, marker=None,
                       offset=None, limit=None):
        session = api_base.get_session()
        query = api_base.model_query(models.Project, session)
        query = self._build_fulltext_search(models.Project, query, q)
        query = self._apply_pagination(
            models.Project, query, marker, offset, limit)

        return query.all()

    def stories_query(self, q, status=None, assignee_id=None,
                      creator_id=None, project_group_id=None, project_id=None,
                      subscriber_id=None, tags=None, updated_since=None,
                      marker=None, offset=None,
                      limit=None, tags_filter_type="all", sort_field='id',
                      sort_dir='asc', current_user=None):
        session = api_base.get_session()

        subquery = stories_api._story_build_query(
            assignee_id=assignee_id,
            creator_id=creator_id,
            project_group_id=project_group_id,
            project_id=project_id,
            tags=tags,
            updated_since=updated_since,
            tags_filter_type=tags_filter_type,
            session=session)

        # Filter by subscriber ID
        if subscriber_id is not None:
            subs = api_base.model_query(models.Subscription)
            subs = api_base.apply_query_filters(query=subs,
                                                model=models.Subscription,
                                                target_type='story',
                                                user_id=subscriber_id)
            subs = subs.subquery()
            subquery = subquery.join(subs, subs.c.target_id == models.Story.id)

        subquery = self._build_fulltext_search(models.Story, subquery, q)

        # Filter out stories that the current user can't see
        subquery = api_base.filter_private_stories(subquery, current_user)

        subquery = subquery.subquery('stories_with_idx')

        query = api_base.model_query(models.StorySummary)\
            .options(subqueryload(models.StorySummary.tags))
        query = query.join(subquery,
                           models.StorySummary.id == subquery.c.stories_id)

        if status:
            query = query.filter(models.StorySummary.status.in_(status))

        query = self._apply_pagination(models.StorySummary,
                                       query,
                                       marker,
                                       offset,
                                       limit,
                                       sort_field=sort_field,
                                       sort_dir=sort_dir)

        return query.all()

    def tasks_query(self, q, story_id=None, assignee_id=None, project_id=None,
                    project_group_id=None, branch_id=None, milestone_id=None,
                    status=None, offset=None, limit=None, current_user=None,
                    sort_field='id', sort_dir='asc'):
        session = api_base.get_session()

        query = tasks_api.task_build_query(
            project_group_id=project_group_id,
            story_id=story_id,
            assignee_id=assignee_id,
            project_id=project_id,
            branch_id=branch_id,
            milestone_id=milestone_id,
            status=status,
            session=session)

        query = self._build_fulltext_search(models.Task, query, q)

        # Filter out stories that the current user can't see
        query = query.outerjoin(models.Story)
        query = api_base.filter_private_stories(query, current_user)

        query = self._apply_pagination(
            models.Task,
            query,
            offset=offset,
            limit=limit,
            sort_field=sort_field,
            sort_dir=sort_dir)

        return query.all()

    def comments_query(self, q, marker=None, offset=None, limit=None,
                       current_user=None, **kwargs):
        session = api_base.get_session()
        query = api_base.model_query(models.Comment, session)
        query = query.outerjoin(models.Story)
        query = api_base.filter_private_stories(query, current_user)

        query = self._build_fulltext_search(models.Comment, query, q)
        query = self._apply_pagination(
            models.Comment, query, marker, offset, limit)

        return query.all()

    def users_query(self, q, marker=None, offset=None, limit=None,
                    filter_non_public=False, **kwargs):
        session = api_base.get_session()
        query = api_base.model_query(models.User, session)
        query = self._build_fulltext_search(models.User, query, q)
        query = self._apply_pagination(
            models.User, query, marker, offset, limit)

        users = query.all()
        if filter_non_public:
            users = [
                api_base._filter_non_public_fields(user, user._public_fields)
                for user in users
            ]

        return users
