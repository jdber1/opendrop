from operator import itemgetter
from typing import TypeVar, Generic, overload, Tuple, Any

import numpy as np
from typing_extensions import Protocol

Image = np.ndarray


class Destroyable(Protocol):
    def destroy(self) -> None:
        """Destroy this object"""


NumericType = TypeVar('NT', int, float, complex)

Vector2 = Tuple[float, float]


class Rect2(Generic[NumericType]):
    @overload
    def __init__(self, *, x0: NumericType, y0: NumericType, x1: NumericType, y1: NumericType): ...

    @overload
    def __init__(self, *, x: NumericType, y: NumericType, w: NumericType, h: NumericType): ...

    @overload
    def __init__(self, *, p0: Tuple[NumericType, NumericType], p1: Tuple[NumericType, NumericType]): ...

    @overload
    def __init__(self, *, pos: Tuple[NumericType, NumericType], size: Tuple[NumericType, NumericType]): ...

    def __init__(self, **kwargs: NumericType):
        if 'x' in kwargs:
            x0, y0 = kwargs.pop('x'), kwargs.pop('y')
            x1, y1 = x0 + kwargs.pop('w'), y0 + kwargs.pop('h')
            if kwargs:
                raise ValueError("Expected only ('x', 'y', 'w', 'h'), got {} extra".format(kwargs.keys()))
        elif 'x0' in kwargs:
            x0, y0 = kwargs.pop('x0'), kwargs.pop('y0')
            x1, y1 = kwargs.pop('x1'), kwargs.pop('y1')
            if kwargs:
                raise ValueError("Expected only ('x0', 'y0', 'x1', 'y1'), got {} extra".format(tuple(kwargs.keys())))
        elif 'p0' in kwargs:
            x0, y0 = kwargs.pop('p0')
            x1, y1 = kwargs.pop('p1')
        elif 'pos' in kwargs:
            (x0, x1), (y0, y1) = ((p, p+s) for p, s in zip(kwargs.pop('pos'), kwargs.pop('size')))
        else:
            raise ValueError('Unrecognised arguments {}'.format(kwargs.keys()))

        self._x0 = x0
        self._y0 = y0
        self._x1 = x1
        self._y1 = y1

        if x0 > x1:
            self._x0, self._x1 = x1, x0

        if y0 > y1:
            self._y0, self._y1 = y1, y0

    @property
    def x0(self) -> NumericType:
        return self._x0

    @property
    def y0(self) -> NumericType:
        return self._y0

    x, y = x0, y0

    @property
    def x1(self) -> NumericType:
        return self._x1

    @property
    def y1(self) -> NumericType:
        return self._y1

    @property
    def w(self) -> NumericType:
        return self.x1 - self.x0

    @property
    def h(self) -> NumericType:
        return self.y1 - self.y0

    @property
    def p0(self) -> Tuple[NumericType, NumericType]:
        return self.x0, self.y0

    @property
    def p1(self) -> Tuple[NumericType, NumericType]:
        return self.x1, self.y1

    pos = p0

    @property
    def size(self) -> Tuple[NumericType, NumericType]:
        return self.w, self.h

    def __repr__(self) -> str:
        return '{class_name}(x0={self.x0}, y0={self.y0}, x1={self.x1}, y1={self.y1})' \
               .format(class_name=type(self).__name__, self=self)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Rect2):
            return False

        return (self.p0 == other.p0) and (self.p1 == other.p1)

    def contains_point(self, point: Vector2, include_boundary: bool = True):
        if include_boundary and (self.x0 <= point[0] <= self.x1 and self.y0 <= point[1] <= self.y1):
            return True
        elif self.x0 < point[0] < self.x1 and self.y0 < point[1] < self.y1:
            return True

        return False

    def is_intersecting(self, other: 'Rect2') -> bool:
        """Return True if this Rect2 is intersecting with `other`. Return False if they do not intersect of if they are
        only 'touching' (i.e. share edges but do not intersect)."""
        if self.x1 > other.x0 and self.x0 < other.x1 and self.y1 > other.y0 and self.y0 < other.y1:
            return True
        else:
            return False
