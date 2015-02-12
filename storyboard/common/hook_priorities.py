# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
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

# This file contains pre-set priorities for our pecan hooks. For more
# information, please see the pecan documentation at
# https://github.com/stackforge/pecan/blob/master/pecan/hooks.py

# Low-level hooks. Example setup db session.
PRE_AUTH = 1

# Authentication must occur relatively early in the hook processing,
# as subsequent logic may depend on ACLs.
AUTH = 10

# Data validation occurs after we've figured out who is making the request,
# but before we perform any cleaning on the data. It's there to make sure
# that we have a sane request.
VALIDATION = 50

# Post validation is there for any hook that is dependent on sane request data.
POST_VALIDATION = 51

# The default notification hook priority is 100. This is set in pecan,
# but we are including it here for the sake of documentation.
DEFAULT = 100
