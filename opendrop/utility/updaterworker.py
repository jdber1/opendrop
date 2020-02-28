# Copyright © 2020, Joseph Berry, Rico Tabor (opendrop.dev@gmail.com)
# OpenDrop is released under the GNU GPL License. You are free to
# modify and distribute the code, but always under the same license
# (i.e. you cannot make commercial derivatives).
#
# If you use this software in your research, please cite the following
# journal articles:
#
# J. D. Berry, M. J. Neeson, R. R. Dagastine, D. Y. C. Chan and
# R. F. Tabor, Measurement of surface and interfacial tension using
# pendant drop tensiometry. Journal of Colloid and Interface Science 454
# (2015) 226–237. https://doi.org/10.1016/j.jcis.2015.05.012
#
# E. Huang, T. Denning, A. Skoufis, J. Qi, R. R. Dagastine, R. F. Tabor
# and J. D. Berry, OpenDrop: Open-source software for pendant drop
# tensiometry & contact angle measurements, submitted to the Journal of
# Open Source Software
#
# These citations help us not only to understand who is using and
# developing OpenDrop, and for what purpose, but also to justify
# continued development of this code and other open source resources.
#
# OpenDrop is distributed WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this software.  If not, see <https://www.gnu.org/licenses/>.


import asyncio
import threading
from typing import Callable, Any, Optional


class UpdaterWorker:
    class _WorkerThread(threading.Thread):
        def __init__(self, do_update: Callable[[], Any], do_shutdown: Callable[[], Any]) -> None:
            super().__init__()
            self._do_update = do_update
            self._do_shutdown = do_shutdown

            self._keep_alive = threading.Event()
            self._is_dying = threading.Event()
            self._busy = threading.Lock()

        def run(self) -> None:
            while True:
                self._keep_alive.clear()
                self._do_update()
                with self._busy:
                    if not self._keep_alive.is_set():
                        self._is_dying.set()
                        self._do_shutdown()
                        break

        def keep_alive(self) -> bool:
            with self._busy:
                if self._is_dying.is_set():
                    return False

                self._keep_alive.set()
                return True

    def __init__(self, do_update: Callable[[], Any], on_idle: Callable[[], Any], *,
                 loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        self._loop = loop or asyncio.get_event_loop()

        self._do_update = do_update

        self._on_idle = on_idle

        self._worker = None  # type: self._WorkerThread
        self._invoke_idle_handler_handle = None  # type: asyncio.Handle

    # Must be called on the main thread.
    def queue_update(self) -> None:
        if self._worker is None:
            self._spawn_worker()
            return

        kept_alive = self._keep_worker_alive()
        if kept_alive:
            return

        self._shutdown_worker()
        self.queue_update()

    def _spawn_worker(self) -> None:
        assert self._worker is None

        if self._invoke_idle_handler_handle is not None:
            self._invoke_idle_handler_handle.cancel()
            self._invoke_idle_handler_handle = None

        self._worker = self._WorkerThread(do_update=self._do_update, do_shutdown=self._shutdown_worker)

        self._worker.start()

    def _keep_worker_alive(self) -> bool:
        assert self._worker is not None
        return self._worker.keep_alive()

    # This method will be run on different threads (could be called by _WorkerThread), so make sure it stays
    # thread-safe.
    def _shutdown_worker(self) -> None:
        assert self._worker is not None

        if threading.current_thread() is not self._worker:
            self._worker.join()

        self._worker = None

        def _invoke_idle_handler():
            self._invoke_idle_handler_handle = None
            self._on_idle()

        if self._invoke_idle_handler_handle is None:
            self._invoke_idle_handler_handle = self._loop.call_soon_threadsafe(_invoke_idle_handler)

    @property
    def is_busy(self) -> bool:
        return self._worker is not None
