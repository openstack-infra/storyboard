# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from sqlalchemy.types import TypeDecorator, DateTime
import pytz


class UTCDateTime(TypeDecorator):
    """This decorator ensures that timezones will always remain attached to
    datetime fields that are written to/from the database, since mysql does
    NOT support timezones in its datetime fields. In the case that a
    value is provided without a timezone, it will raise an exception to draw
    attention to itself: Engineers should always work with timezoned
    datetime instances.
    """
    impl = DateTime

    def process_bind_param(self, value, engine):
        if value is not None:
            # If the value doesn't have a timezone, raise an exception.
            if not value.tzinfo:
                raise RuntimeError("Datetime value without timezone provided,"
                                   " please provide a timezone.")

            # Convert to UTC, then scrub the timezone for storing in MySQL.
            return value.astimezone(pytz.utc).replace(tzinfo=None)

    def process_result_value(self, value, engine):
        if value is not None:
            return value.replace(tzinfo=pytz.utc)
