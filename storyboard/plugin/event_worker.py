# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
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
# implied. See the License for the specific language governing permissions and
# limitations under the License.

import abc
from multiprocessing import Process
import signal
from threading import Timer

from oslo_config import cfg
from oslo_log import log

import storyboard.db.api.base as db_api
from storyboard.notifications.notification_hook import class_mappings
from storyboard.notifications.subscriber import subscribe
from storyboard.openstack.common.gettextutils import _LI, _LW  # noqa
from storyboard.plugin.base import PluginBase

CONF = cfg.CONF
LOG = log.getLogger(__name__)
MANAGER = None

IMPORT_OPTS = [
    cfg.IntOpt("worker-count",
               default="5",
               help="The number of workers to spawn and manage.")
]


def run_daemon():
    """Start the daemon manager.
    """
    global MANAGER

    CONF.register_cli_opts(IMPORT_OPTS)

    try:
        log.register_options(CONF)
    except cfg.ArgsAlreadyParsedError:
        pass

    log.setup(CONF, 'storyboard')
    CONF(project='storyboard')

    signal.signal(signal.SIGTERM, terminate)
    signal.signal(signal.SIGINT, terminate)

    MANAGER = DaemonManager(daemon_method=subscribe,
                            child_process_count=CONF.worker_count)
    MANAGER.start()


def terminate(signal, frame):
    # This assumes that all the child processes will terminate gracefully
    # on a SIGINT
    global MANAGER
    MANAGER.stop()

    # Raise SIGINT to all child processes.
    signal.default_int_handler()


class DaemonManager():
    """A Daemon manager to handle multiple subprocesses.
    """
    def __init__(self, child_process_count, daemon_method):
        """Create a new daemon manager with N processes running the passed
        method. Once start() is called, The daemon method will be spawned N
        times and continually checked/restarted until the process is
        interrupted either by a system exit or keyboard interrupt.

        :param child_process_count: The number of child processes to spawn.
        :param daemon_method: The method to run in the child process.
        """

        # Number of child procs.
        self._child_process_count = child_process_count

        # Process management threads.
        self._procs = list()

        # Save the daemon method
        self._daemon_method = daemon_method

        # Health check timer
        self._timer = PerpetualTimer(1, self._health_check)

    def _health_check(self):
        processes = list(self._procs)
        dead_processes = 0

        for process in processes:
            if not process.is_alive():
                LOG.warning(_LW("Dead Process found [exit code:%d]") %
                            (process.exitcode,))
                dead_processes += 1
                self._procs.remove(process)

        for i in range(dead_processes):
            self._add_process()

    def start(self):
        """Start the daemon manager and spawn child processes.
        """
        LOG.info(_LI("Spawning %s child processes") %
                 (self._child_process_count,))
        self._timer.start()
        for i in range(self._child_process_count):
            self._add_process()

    def stop(self):
        self._timer.cancel()

        processes = list(self._procs)
        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join()
            self._procs.remove(process)

    def _add_process(self):
        process = Process(target=self._daemon_method)
        process.start()
        self._procs.append(process)


class PerpetualTimer():
    """A timer wrapper class that repeats itself.
    """

    def __init__(self, t, handler):
        self.t = t
        self.handler = handler
        self.thread = Timer(self.t, self.handle_function)

    def handle_function(self):
        self.handler()
        self.thread = Timer(self.t, self.handle_function)
        self.thread.setDaemon(True)
        self.thread.start()

    def start(self):
        self.thread.start()

    def cancel(self):
        self.thread.cancel()


class WorkerTaskBase(PluginBase):
    """Base class for a worker that listens to API Events."""

    __metaclass__ = abc.ABCMeta

    def event(self, author_id, method, path, status, resource, resource_id,
              sub_resource=None, sub_resource_id=None,
              resource_before=None, resource_after=None):
        """Handle an event.

        A database session is created, and passed to the abstract method.
        """
        session = db_api.get_session(in_request=False)

        with session.begin(subtransactions=True):
            author = self.resolve_resource_by_name(session, 'user', author_id)

            self.handle(session=session,
                        author=author,
                        method=method,
                        path=path,
                        status=status,
                        resource=resource,
                        resource_id=resource_id,
                        sub_resource=sub_resource,
                        sub_resource_id=sub_resource_id,
                        resource_before=resource_before,
                        resource_after=resource_after)

    def resolve_resource_by_name(self, session, resource_name, resource_id):
        if resource_name not in class_mappings:
            return None

        klass = class_mappings[resource_name][0]
        return db_api.entity_get(klass, resource_id, session=session)

    @abc.abstractmethod
    def handle(self, session, author, method, path, status, resource,
               resource_id, sub_resource=None, sub_resource_id=None,
               resource_before=None, resource_after=None):
        """Handle an event.

        :param session: An event-specific SQLAlchemy session.
        :param author: The author's user record.
        :param method: The HTTP Method.
        :param path: The full HTTP Path requested.
        :param status: The returned HTTP Status of the response.
        :param resource: The resource type.
        :param resource_id: The ID of the resource.
        :param sub_resource: The subresource type.
        :param sub_resource_id: The ID of the subresource.
        :param resource_before: The resource state before this event occurred.
        :param resource_after: The resource state after this event occurred.
        """
