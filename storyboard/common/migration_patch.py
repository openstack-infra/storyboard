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

# Stolen from Sergey Lukjanov

import copy
import uuid

from alembic import op
import six
import sqlalchemy


ORIGINAL_DROP = op.drop_column


def patch(cfg):
    """Patch all needed stuff for running migrations.

    Currently, we're patching:

    * drop_column for sqlite driver.
    """

    op.drop_column = _drop_dispatch


def _drop_dispatch(table_name, column_name):
    connection = op.get_bind()
    if 'sqlite' in str(connection.engine.url):
        return _sqlite_drop_column(table_name, column_name)
    else:
        return ORIGINAL_DROP(table_name, column_name)


def _sqlite_drop_column(table_name, column_name):
    """It implements DROP COLUMN for SQLite.

    The DROP COLUMN command isn't supported by SQLite specification.
    Instead of calling DROP COLUMN it uses the following workaround:

    * create temp table '{table_name}_{rand_uuid}' w/o dropped column;
    * copy all data with remaining columns to the temp table;
    * drop old table;
    * rename temp table to the old table name.
    """

    connection = op.get_bind()
    meta = sqlalchemy.MetaData(bind=connection)
    meta.reflect()

    # construct lists of all needed columns and their names
    column_names = []  # names of remaining columns
    binded_columns = []  # list of columns with table reference
    unbound_columns = []  # list of columns without table reference

    for column in meta.tables[table_name].columns:
        if column.name == column_name:
            continue
        column_names.append(column.name)
        binded_columns.append(column)
        unbound_column = copy.copy(column)
        unbound_column.table = None
        unbound_columns.append(unbound_column)

    # create temp table
    tmp_table_name = "%s_%s" % (table_name, six.text_type(uuid.uuid4()))
    op.create_table(tmp_table_name, *unbound_columns)
    meta.reflect()

    # copy data from the old table to the temp one
    sql_select = sqlalchemy.sql.select(binded_columns)
    connection.execute(sqlalchemy.sql.insert(meta.tables[tmp_table_name])
                       .from_select(column_names, sql_select))

    # drop the old table and rename temp table to the old table name
    op.drop_table(table_name)
    op.rename_table(tmp_table_name, table_name)
