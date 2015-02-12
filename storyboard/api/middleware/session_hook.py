# Copyright (c) 2015 Mirantis Inc.
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

from pecan import hooks
from pecan import request
from sqlalchemy.exc import InvalidRequestError

import storyboard.common.hook_priorities as priority
from storyboard.db.api import base


class DBSessionHook(hooks.TransactionHook):

    priority = priority.PRE_AUTH

    def _start_session(self):
        # in_request is False because at this point we need a new session
        session = base.get_session(autocommit=False, in_request=False)
        request.session = session

    def _commit_session(self):
        if hasattr(request, "session"):
            # Commit the session
            try:
                request.session.commit()
                request.session.flush()
            except InvalidRequestError:
                # Session may have got into error state after a rollback was
                # called for a failed create or update. Skipping.
                pass

    def _rollback_session(self):
        if hasattr(request, "session"):
            try:
                request.session.rollback()
                request.session.close()
            except InvalidRequestError:
                # There may be no transactions to roll back. Skipping.
                pass

    def _clear_session(self):
        if hasattr(request, "session"):
            request.session.close()

    def is_transactional(self, state):
        return True

    def __init__(self):
        super(DBSessionHook, self).__init__(self._start_session,
                                            self._start_session,
                                            self._commit_session,
                                            self._rollback_session,
                                            self._clear_session)
