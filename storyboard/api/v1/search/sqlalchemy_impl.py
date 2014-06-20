# Copyright (c) 2014 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from oslo.db.sqlalchemy import utils
from sqlalchemy_fulltext import FullTextSearch
import sqlalchemy_fulltext.modes as FullTextMode

from storyboard.api.v1.search import search_engine
from storyboard.db.api import base as api_base
from storyboard.db import models


class SqlAlchemySearchImpl(search_engine.SearchEngine):

    def _build_fulltext_search(self, model_cls, query, q):
        query = query.filter(FullTextSearch(q, model_cls,
                                            mode=FullTextMode.NATURAL))

        return query

    def _apply_pagination(self, model_cls, query, marker=None, limit=None):

        marker_entity = None
        if marker:
            marker_entity = api_base.entity_get(model_cls, marker, True)

        return utils.paginate_query(query=query,
                                    model=model_cls,
                                    limit=limit,
                                    sort_keys=["id"],
                                    marker=marker_entity)

    def projects_query(self, q, sort_dir=None, marker=None, limit=None):
        session = api_base.get_session()
        query = api_base.model_query(models.Project, session)
        query = self._build_fulltext_search(models.Project, query, q)
        query = self._apply_pagination(models.Project, query, marker, limit)

        return query.all()

    def stories_query(self, q, marker=None, limit=None, **kwargs):
        session = api_base.get_session()
        query = api_base.model_query(models.Story, session)
        query = self._build_fulltext_search(models.Story, query, q)
        query = self._apply_pagination(models.Story, query, marker, limit)

        return query.all()

    def tasks_query(self, q, marker=None, limit=None, **kwargs):
        session = api_base.get_session()
        query = api_base.model_query(models.Task, session)
        query = self._build_fulltext_search(models.Task, query, q)
        query = self._apply_pagination(models.Task, query, marker, limit)

        return query.all()

    def comments_query(self, q, marker=None, limit=None, **kwargs):
        session = api_base.get_session()
        query = api_base.model_query(models.Comment, session)
        query = self._build_fulltext_search(models.Comment, query, q)
        query = self._apply_pagination(models.Comment, query, marker, limit)

        return query.all()

    def users_query(self, q, marker=None, limit=None, **kwargs):
        session = api_base.get_session()
        query = api_base.model_query(models.User, session)
        query = self._build_fulltext_search(models.User, query, q)
        query = self._apply_pagination(models.User, query, marker, limit)

        return query.all()
