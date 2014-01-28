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

from datetime import datetime


class FakeSession(object):
    def __init__(self):
        self.objects_by_type = dict()
        self.max_id = 1

    def add(self, obj):
        obj_type = type(obj)
        if obj_type not in self.objects_by_type:
            self.objects_by_type[obj_type] = list()
        if obj in self.objects_by_type[obj_type]:
            return

        setattr(obj, "id", self.max_id)
        self.max_id += 1

        setattr(obj, "created_at", datetime.now())

        self.objects_by_type[obj_type].append(obj)

    def query(self, obj_type):
        return FakeQuery(self.objects_by_type.get(obj_type, []))

    def begin(self):
        return self

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class FakeQuery(object):
    def __init__(self, obj_list):
        self.obj_list = obj_list

    def filter_by(self, **kwargs):
        filtered_list = []
        for obj in self.obj_list:
            matches = True
            for k, v in kwargs.iteritems():
                if getattr(obj, k) != v:
                    matches = False
                    break

            if matches:
                filtered_list.append(obj)

        return FakeFilterResult(filtered_list)


class FakeFilterResult(object):
    def __init__(self, obj_list):
        self.obj_list = obj_list

    def first(self):
        try:
            return self.obj_list[0]
        except Exception:
            return None

    def all(self):
        return self.obj_list
