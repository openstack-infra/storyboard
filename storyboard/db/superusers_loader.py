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

import warnings
import yaml

from sqlalchemy.exc import SADeprecationWarning

from storyboard._i18n import _
from storyboard.db.api import base as db_api
from storyboard.db.models import User

warnings.simplefilter("ignore", SADeprecationWarning)


def do_load_models(filename):

    config_file = open(filename)
    superusers_list = yaml.load(config_file)

    session = db_api.get_session(in_request=False)

    with session.begin():
        for user in superusers_list:
            openid = user.get("openid")
            if not openid:
                raise Exception(_("A superuser is missing an openid field"))

            email = user.get("email") or "unset"

            db_user = session.query(User).filter_by(openid=openid).first()
            if not db_user:
                db_user = User()
                db_user.openid = openid
                db_user.email = email

            db_user.is_superuser = True

            session.add(db_user)
