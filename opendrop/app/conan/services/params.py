from typing import Optional, NamedTuple

from gi.repository import GObject

from opendrop.geometry import Rect2, Line2


class ConanParamsFactory(GObject.Object):
    _baseline: Optional[Line2] = None
    _thresh: float = 0.5
    _inverted: bool = False
    _roi: Optional[Rect2[int]] = None

    def create(self) -> 'ConanParams':
        return ConanParams(
            baseline=self._baseline,
            thresh=self._thresh,
            inverted=self._inverted,
            roi=self._roi,
        )

    @GObject.Signal
    def changed(self) -> None:
        """Emitted when parameters are changed."""

    @GObject.Property
    def baseline(self) -> Optional[Line2]:
        return self._baseline

    @baseline.setter
    def baseline(self, line: Optional[Line2]) -> None:
        self._baseline = line
        self.changed.emit()

    @GObject.Property
    def thresh(self) -> float:
        return self._thresh

    @thresh.setter
    def thresh(self, thresh: float) -> None:
        self._thresh = thresh
        self.changed.emit()

    @GObject.Property
    def inverted(self) -> bool:
        return self._inverted

    @inverted.setter
    def inverted(self, value: bool) -> None:
        self._inverted = value
        self.changed.emit()

    @GObject.Property
    def roi(self) -> Optional[Rect2[int]]:
        return self._roi

    @roi.setter
    def roi(self, region: Optional[Rect2[int]]) -> None:
        self._roi = region
        self.changed.emit()


class ConanParams(NamedTuple):
    """Plain Old Data structure"""

    baseline: Optional[Line2]
    thresh: float
    inverted: bool
    roi: Optional[Rect2[int]]
