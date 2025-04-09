from typing import Optional

from gi.repository import GObject

from opendrop.geometry import Line2


class BaselineFactory(GObject.Object):
    _baseline: Optional[Line2] = None

    def create(self) -> Optional[Line2]:
        return self._baseline

    @GObject.Signal
    def changed(self) -> None:
        """Emitted when baseline is changed."""

    @GObject.Property
    def baseline(self) -> Optional[Line2]:
        return self._baseline

    @baseline.setter
    def baseline(self, line: Optional[Line2]) -> None:
        self._baseline = line
        self.changed.emit()
