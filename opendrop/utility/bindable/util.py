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
#E. Huang, T. Denning, A. Skoufis, J. Qi, R. R. Dagastine, R. F. Tabor
#and J. D. Berry, OpenDrop: Open-source software for pendant drop
#tensiometry & contact angle measurements, submitted to the Journal of
# Open Source Software
#
#These citations help us not only to understand who is using and
#developing OpenDrop, and for what purpose, but also to justify
#continued development of this code and other open source resources.
#
# OpenDrop is distributed WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this software.  If not, see <https://www.gnu.org/licenses/>.
import asyncio
import threading
from typing import Any, Iterable, Callable, Optional, Container

from opendrop.utility.bindable import AccessorBindable


class ThreadSafeBindableCollection:
    _fields = tuple()

    class Editor:
        def __init__(self, fields: Container[str], do_commit: Callable[[], Any], do_discard: Callable[[], Any]) -> None:
            self._fields = fields

            self._do_commit = do_commit
            self._do_discard = do_discard

            self._changes = {}

        def set_value(self, name: str, value: Any) -> None:
            if name not in self._fields:
                raise ValueError("No field named '{}'".format(name))

            self._changes[name] = value

        def commit(self) -> None:
            self._do_commit()

        def discard(self) -> None:
            self._do_discard()

    # The `_loop` parameter is preceded by an underscore to avoid naming conflicts with initial values.
    def __init__(self, *, _loop: Optional[asyncio.AbstractEventLoop] = None, **initial_values) -> None:
        self._loop = _loop or asyncio.get_event_loop()

        self._accessors = {
            name: AccessorBindable(getter=lambda name=name: self._get_value(name))
            for name in self._fields
        }

        self._values = initial_values
        assert set(self._values.keys()) == set(self._fields)

        self._editor = None
        self._editor_lock = threading.Lock()
        self._read_lock = threading.Lock()

    def _get_value(self, name: str) -> Any:
        with self._read_lock:
            return self._values[name]

    def edit(self, blocking: bool = True, timeout: float = -1) -> Optional[Editor]:
        if not self._editor_lock.acquire(blocking=blocking, timeout=timeout):
            return None

        assert self._editor is None
        self._editor = self.Editor(fields=self._fields, do_commit=self._commit_edit, do_discard=self._discard_edit)

        return self._editor

    def _commit_edit(self) -> None:
        editor = self._editor
        assert editor is not None
        assert self._editor_lock.locked()

        with self._read_lock:
            self._values.update(editor._changes)

        changed = tuple(editor._changes.keys())

        self._release_editor()

        def do_pokes():
            for name in changed:
                getattr(self, name).poke()
        self._loop.call_soon_threadsafe(do_pokes)

    def _discard_edit(self) -> None:
        editor = self._editor
        assert editor is not None
        assert self._editor_lock.locked()

        self._release_editor()

    def _release_editor(self) -> None:
        self._editor = None
        self._editor_lock.release()

    def __getattr__(self, name: str) -> Any:
        try:
            return self._accessors[name]
        except KeyError:
            raise AttributeError("No field named '{}'".format(name))


def thread_safe_bindable_collection(fields: Iterable[str]):
    class UserThreadSafeBindableCollection(ThreadSafeBindableCollection):
        _fields = tuple(fields)

    return UserThreadSafeBindableCollection
