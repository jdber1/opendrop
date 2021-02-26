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


from abc import abstractmethod
import math
import operator
from typing import Any, Callable, Generic, Iterable, Sequence, Tuple, TypeVar, overload

from typing import Literal, Protocol


T_co = TypeVar('T_co', covariant=True)
U_co = TypeVar('U_co', covariant=True)

T_contra = TypeVar('T_contra', contravariant=True)


class Add(Protocol[T_contra, U_co]):
    def __add__(self, other: T_contra) -> U_co: ...


class RAdd(Protocol[T_contra, U_co]):
    def __radd__(self, other: T_contra) -> U_co: ...


class Mul(Protocol[T_contra, U_co]):
    def __mul__(self, other: T_contra) -> U_co: ...


class RMul(Protocol[T_contra, U_co]):
    def __rmul__(self, other: T_contra) -> U_co: ...


class Sub(Protocol[T_contra, U_co]):
    def __sub__(self, other: T_contra) -> U_co: ...


class RSub(Protocol[T_contra, U_co]):
    def __rsub__(self, other: T_contra) -> U_co: ...


class TrueDiv(Protocol[T_contra, U_co]):
    def __truediv__(self, other: T_contra) -> U_co: ...


class RTrueDiv(Protocol[T_contra, U_co]):
    def __rtruediv__(self, other: T_contra) -> U_co: ...


class FloorDiv(Protocol[T_contra, U_co]):
    def __floordiv__(self, other: T_contra) -> U_co: ...


class RFloorDiv(Protocol[T_contra, U_co]):
    def __rfloordiv__(self, other: T_contra) -> U_co: ...


class Neg(Protocol[T_co]):
    def __neg__(self) -> T_co: ...


class Pos(Protocol[T_co]):
    def __pos__(self) -> T_co: ...


class Comparable(Protocol[T_contra]):
    def __lt__(self, other: T_contra) -> bool: ...

    def __gt__(self, other: T_contra) -> bool: ...

    def __le__(self, other: T_contra) -> bool: ...

    def __ge__(self, other: T_contra) -> bool: ...


class Number(
    Add,
    Sub,
    Mul,
    TrueDiv,
    Neg,
    Pos,
    Comparable,
    Protocol,
): ...


A_co = TypeVar('A_co', bound=Number, covariant=True)
B = TypeVar('B', bound=Number)
C = TypeVar('C', bound=Number)


class _Vector2(Tuple[T_co, T_co]):
    @property
    @abstractmethod
    def x(self) -> T_co:
        return super().__getitem__(0)

    @property
    @abstractmethod
    def y(self) -> T_co:
        return super().__getitem__(1)

    @abstractmethod
    def __getitem__(self, index: Literal[0, 1]) -> T_co:
        return super().__getitem__(index)

    def __len__(self) -> Literal[2]:
        return 2


class Vector2(_Vector2[A_co]):
    @overload
    def __new__(cls, x: A_co, y: A_co) -> 'Vector2[A_co]': ...
    @overload
    def __new__(cls, iterable: Iterable[A_co]) -> 'Vector2[A_co]': ...

    def __new__(cls, *args, **kwargs):
        if len(args) == 1:
            return cls._from_iterable(*args)
        elif len(args) == 2:
            return cls._from_xy(*args)
        elif 'x' in kwargs and 'y' in kwargs:
            return cls._from_xy(**kwargs)
        elif 'iterable' in kwargs:
            return cls._from_iterable(**kwargs)
        else:
            raise TypeError(
                    'No {} constructor found with {} positional arguments and {} keyword arguments'
                    .format(cls.__name__, len(args), tuple(kwargs.keys()))
            )

    @classmethod
    def _from_xy(cls, x: A_co, y: A_co) -> 'Vector2[A_co]':
        return super().__new__(cls, (x, y))

    @classmethod
    def _from_iterable(cls, iterable: Iterable[A_co]) -> 'Vector2[A_co]':
        x, y = iterable
        return cls._from_xy(x, y)

    def replace(self: 'Vector2[B]', **kwargs: B) -> 'Vector2[B]':
        unexpected_names = set(kwargs.keys()) - {'x', 'y'}
        if unexpected_names:
            raise ValueError(
                    'Got unexpected field names: {!r}'
                    .format(list(unexpected_names))
            )

        new_x = self.x
        new_y = self.y

        if 'x' in kwargs:
            new_x = kwargs['x']
        elif 'y' in kwargs:
            new_y = kwargs['y']

        return Vector2(new_x, new_y)

    def map(self, func: Callable[[A_co], B]) -> 'Vector2[B]':
        return Vector2(map(func, self))

    def __neg__(self: _Vector2[Neg[B]]) -> 'Vector2[B]':
        try:
            return Vector2(map(operator.neg, self))
        except TypeError:
            return NotImplemented

    def __pos__(self: _Vector2[Pos[B]]) -> 'Vector2[B]':
        try:
            return Vector2(map(operator.pos, self))
        except TypeError:
            return NotImplemented

    @overload
    def __add__(self: _Vector2[Add[B, C]], other: Sequence[B]) -> 'Vector2[C]': ...
    @overload
    def __add__(self, other: Sequence[RAdd[A_co, B]]) -> 'Vector2[B]': ...

    def __add__(self, other):
        try:
            if len(other) != 2:
                return NotImplemented

            return Vector2(map(operator.add, self, other))
        except TypeError:
            return NotImplemented

    @overload
    def __radd__(self: _Vector2[RAdd[B, C]], other: Sequence[B]) -> 'Vector2[C]': ...
    @overload
    def __radd__(self, other: Sequence[Add[A_co, B]]) -> 'Vector2[B]': ...

    def __radd__(self, other):
        try:
            if len(other) != 2:
                return NotImplemented

            return Vector2(map(operator.add, other, self))
        except TypeError:
            return NotImplemented

    @overload
    def __sub__(self: _Vector2[Sub[B, C]], other: Sequence[B]) -> 'Vector2[C]': ...
    @overload
    def __sub__(self, other: Sequence[RSub[A_co, B]]) -> 'Vector2[B]': ...

    def __sub__(self, other):
        try:
            if len(other) != 2:
                return NotImplemented

            return Vector2(map(operator.sub, self, other))
        except TypeError:
            return NotImplemented

    @overload
    def __rsub__(self: _Vector2[RSub[B, C]], other: Sequence[B]) -> 'Vector2[C]': ...
    @overload
    def __rsub__(self, other: Sequence[Sub[A_co, B]]) -> 'Vector2[B]': ...

    def __rsub__(self, other):
        try:
            if len(other) != 2:
                return NotImplemented

            return Vector2(map(operator.sub, other, self))
        except TypeError:
            return NotImplemented

    @overload
    def __mul__(self: _Vector2[Mul[B, C]], other: B) -> 'Vector2[C]': ...

    @overload
    def __mul__(self, other: RMul[A_co, B]) -> 'Vector2[B]': ...

    @overload
    def __mul__(self: _Vector2[Mul[B, C]], other: Sequence[B]) -> 'Vector2[C]': ...

    @overload
    def __mul__(self, other: Sequence[RMul[A_co, B]]) -> 'Vector2[B]': ...

    def __mul__(self, other):
        try:
            if isiterable(other):
                if len(other) != 2:
                    return NotImplemented
                return self._elementwise_mul(other)
            else:
                return Vector2(x*other for x in self)
        except TypeError:
            return NotImplemented

    def _elementwise_mul(self: _Vector2[Mul[B, C]], other: Sequence[B]) -> 'Vector2[C]':
        return Vector2(map(operator.mul, self, other))

    @overload
    def __rmul__(self: _Vector2[RMul[B, C]], other: B) -> 'Vector2[C]': ...

    @overload
    def __rmul__(self, other: Mul[A_co, B]) -> 'Vector2[B]': ...

    @overload
    def __rmul__(self: _Vector2[RMul[B, C]], other: Sequence[B]) -> 'Vector2[C]': ...

    @overload
    def __rmul__(self, other: Sequence[Mul[A_co, B]]) -> 'Vector2[B]': ...

    def __rmul__(self, other):
        try:
            if isiterable(other):
                if len(other) != 2:
                    return NotImplemented
                return self._elementwise_rmul(other)
            else:
                return Vector2(other*x for x in self)
        except TypeError:
            return NotImplemented

    def _elementwise_rmul(self: _Vector2[RMul[B, C]], other: Sequence[B]) -> 'Vector2[C]':
        return Vector2(map(operator.mul, other, self))

    @overload
    def __truediv__(self: _Vector2[TrueDiv[B, C]], other: B) -> 'Vector2[C]': ...
    @overload
    def __truediv__(self, other: RTrueDiv[A_co, B]) -> 'Vector2[B]': ...

    def __truediv__(self, other):
        try:
            return Vector2(x/other for x in self)
        except TypeError:
            return NotImplemented

    @overload
    def __floordiv__(self: _Vector2[FloorDiv[B, C]], other: B) -> 'Vector2[C]': ...
    @overload
    def __floordiv__(self, other: RFloorDiv[A_co, B]) -> 'Vector2[B]': ...

    def __floordiv__(self, other):
        try:
            return Vector2(x//other for x in self)
        except TypeError:
            return NotImplemented

    def __abs__(self) -> float:
        return (abs(self.x)**2 + abs(self.y)**2)**0.5

    def __repr__(self) -> str:
        return '{class_name}({x}, {y})'.format(
                class_name=type(self).__name__,
                x=self[0],
                y=self[1],
        )


class _Rect2(Generic[T_co]):
    def __init__(self, x0: T_co, y0: T_co, x1: T_co, y1: T_co) -> None:
        self._x0 = x0
        self._y0 = y0
        self._x1 = x1
        self._y1 = y1

    @property
    def x0(self) -> T_co:
        return self._x0

    @property
    def y0(self) -> T_co:
        return self._y0

    @property
    def x1(self) -> T_co:
        return self._x1

    @property
    def y1(self) -> T_co:
        return self._y1


class Rect2(_Rect2[A_co]):
    @overload
    def __init__(self, iterable: Iterable[A_co]) -> None: ...
    @overload
    def __init__(self, x0: A_co, y0: A_co, x1: A_co, y1: A_co) -> None: ...
    @overload
    def __init__(self, pt0: Iterable[A_co], pt1: Iterable[A_co]) -> None: ...
    @overload
    def __init__(self, *, x: A_co, y: A_co, w: A_co, h: A_co) -> None: ...
    @overload
    def __init__(self, *, x: A_co, y: A_co, width: A_co, height: A_co) -> None: ...
    @overload
    def __init__(self, *, position: Iterable[A_co], size: Iterable[A_co]) -> None: ...

    def __init__(self, *args, **kwargs):
        if len(args) == 1:
            return self._from_iterable(*args)
        elif len(args) == 4:
            return self._from_x0y0x1y1(*args)
        elif len(args) == 2:
            return self._from_pt0pt1(*args)
        elif 'x0' in kwargs:
            return self._from_x0y0x1y1(**kwargs)
        elif 'x' in kwargs and 'w' in kwargs:
            return self._from_xywh(**kwargs)
        elif 'x' in kwargs and 'width' in kwargs:
            args = (kwargs['x'], kwargs['y'], kwargs['width'], kwargs['height'])
            return self._from_xywh(*args)
        elif 'pt0' in kwargs:
            return self._from_pt0pt1(**kwargs)
        elif 'position' in kwargs:
            return self._from_position_and_size(**kwargs)
        else:
            raise TypeError(
                    'No {} constructor found with {} positional arguments and {} keyword arguments'
                    .format(type(self).__name__, len(args), tuple(kwargs.keys()))
            )

    def _from_x0y0x1y1(self, x0: A_co, y0: A_co, x1: A_co, y1: A_co) -> None:
        if x0 > x1:
            x0, x1 = x1, x0

        if y0 > y1:
            y0, y1 = y1, y0

        super().__init__(x0, y0, x1, y1)

    def _from_pt0pt1(self, pt0: Iterable[A_co], pt1: Iterable[A_co]) -> None:
        x0, y0 = pt0
        x1, y1 = pt1
        self._from_x0y0x1y1(x0, y0, x1, y1)

    def _from_xywh(self, x: A_co, y: A_co, w: A_co, h: A_co) -> None:
        x0, y0 = x, y
        x1, y1 = x+w, y+h
        self._from_x0y0x1y1(x0, y0, x1, y1)

    def _from_position_and_size(self, position: Iterable[A_co], size: Iterable[A_co]) -> None:
        x, y = position
        w, h = size
        self._from_xywh(x, y, w, h)

    def _from_iterable(self, iterable: Iterable[A_co]) -> None:
        x0, y0, x1, y1 = iterable
        self._from_x0y0x1y1(x0, y0, x1, y1)

    @property
    def pt0(self) -> Vector2[A_co]:
        return Vector2(self.x0, self.y0)

    @property
    def pt1(self) -> Vector2[A_co]:
        return Vector2(self.x1, self.y1)

    @property
    def x(self) -> A_co:
        return self.x0

    @property
    def y(self) -> A_co:
        return self.y0

    @property
    def xc(self) -> A_co:
        return (self.x0 + self.x1)/2

    @property
    def yc(self) -> A_co:
        return (self.y0 + self.y1)/2

    @property
    def w(self) -> A_co:
        return self.x1 - self.x0

    @property
    def h(self) -> A_co:
        return self.y1 - self.y0

    @property
    def width(self) -> A_co:
        return self.w

    @property
    def height(self) -> A_co:
        return self.h

    @property
    def position(self) -> Vector2[A_co]:
        return Vector2(self.x, self.y)

    @property
    def center(self) -> Vector2[A_co]:
        return Vector2(self.xc, self.yc)

    @property
    def size(self) -> Vector2[A_co]:
        return Vector2(self.w, self.h)

    def replace(self: 'Rect2[B]', **kwargs: B) -> 'Rect2[B]':
        raise NotImplementedError

    def map(self, func: Callable[[A_co], B]) -> 'Rect2[B]':
        return Rect2(map(func, self))

    def __repr__(self) -> str:
        return '{class_name}(x0={x0}, y0={y0}, x1={x1}, y1={y1})' \
               .format(class_name=type(self).__name__, x0=self.x0, y0=self.y0, x1=self.x1, y1=self.y1)

    @overload
    def contains(self: _Rect2[Comparable[B]], point: Iterable[B], include_boundary: bool = True) -> bool: ...
    @overload
    def contains(self, point: Iterable[Comparable[A_co]], include_boundary: bool = True) -> bool: ...

    def contains(self, point, include_boundary=True):
        point_vec = Vector2(point)
        if include_boundary:
            return self.x0 <= point_vec.x <= self.x1 and self.y0 <= point_vec.y <= self.y1
        else:
            return self.x0 < point_vec.x < self.x1 and self.y0 < point_vec.y < self.y1

    @overload
    def intersects(self: _Rect2[Comparable[B]], other: Iterable[B]) -> bool: ...
    @overload
    def intersects(self, other: Iterable[Comparable[A_co]]) -> bool: ...

    def intersects(self, other):
        """Return True if this Rect2 is intersecting with the `other` Rect2. Return False if they do not
        intersect or if they are only 'touching' (i.e. share edges)."""
        other = Rect2(other)
        return self.x1 > other.x0 and self.x0 < other.x1 and self.y1 > other.y0 and self.y0 < other.y1

    @overload
    def __add__(self: _Rect2[Add[B, C]], other: Sequence[B]) -> 'Rect2[C]': ...
    @overload
    def __add__(self, other: Sequence[RAdd[A_co, B]]) -> 'Rect2[B]': ...

    def __add__(self, other):
        try:
            t = Vector2(other)
            return Rect2(self.pt0 + t, self.pt1 + t)
        except TypeError:
            return NotImplemented

    @overload
    def __radd__(self: _Rect2[RAdd[B, C]], other: Sequence[B]) -> 'Rect2[C]': ...
    @overload
    def __radd__(self, other: Sequence[Add[A_co, B]]) -> 'Rect2[B]': ...

    def __radd__(self, other):
        try:
            t = Vector2(other)
            return Rect2(t + self.pt0, t + self.pt1)
        except TypeError:
            return NotImplemented

    @overload
    def __sub__(self: _Rect2[Sub[B, C]], other: Sequence[B]) -> 'Rect2[C]': ...
    @overload
    def __sub__(self, other: Sequence[RSub[A_co, B]]) -> 'Rect2[B]': ...

    def __sub__(self, other):
        try:
            t = Vector2(other)
            return Rect2(self.pt0 - t, self.pt1 - t)
        except TypeError:
            return NotImplemented

class Line2:
    def __init__(self, pt0: Iterable[float], pt1: Iterable[float]) -> None:
        pt0_vec = Vector2(pt0)
        pt1_vec = Vector2(pt1)

        if pt0_vec == pt1_vec:
            raise ValueError("pt0 and pt1 cannot be equal")

        self._pt0 = pt0_vec
        self._pt1 = pt1_vec

    @property
    def pt0(self) -> Vector2[float]:
        return self._pt0

    @property
    def pt1(self) -> Vector2[float]:
        return self._pt1

    @property
    def unit(self) -> Vector2[float]:
        unit = self.pt1 - self.pt0
        unit /= abs(unit)
        return unit

    @property
    def perp(self) -> Vector2[float]:
        unit = self.unit
        perp = Vector2(-unit.y, unit.x)
        return perp

    @property
    def gradient(self) -> float:
        dx = self._pt1[0] - self._pt0[0]
        dy = self._pt1[1] - self._pt0[1]

        if dx == 0:
            return math.copysign(dy, math.inf)

        return dy/dx

    @overload
    def eval(self, *, x: float) -> Vector2[float]: ...
    @overload
    def eval(self, *, y: float) -> Vector2[float]: ...

    def eval(self, **kwargs):
        if 'x' in kwargs:
            x = kwargs['x']
            return Vector2(x, self.solve(x=x))
        elif 'y' in kwargs:
            y = kwargs['y']
            return Vector2(self.solve(y=y), y)
        else:
            raise TypeError

    @overload
    def solve(self, *, x: float) -> float: ...
    @overload
    def solve(self, *, y: float) -> float: ...

    def solve(self, **kwargs):
        if 'x' in kwargs:
            return self._solve_for_y(**kwargs)
        elif 'y' in kwargs:
            return self._solve_for_x(**kwargs)
        else:
            raise TypeError

    def _solve_for_y(self, x: float) -> float:
        dx = x - self._pt0.x
        dy = dx * self.gradient
        return self._pt0.y + dy

    def _solve_for_x(self, y: float) -> float:
        dy = y - self._pt0.y

        if self.gradient == 0:
            x = math.copysign(dy, math.inf)
            return x

        dx = dy / self.gradient
        return self._pt0.x + dx

    def __add__(self, other: Sequence[float]) -> 'Line2':
        try:
            translate = Vector2(other)
            return Line2(self.pt0 + translate, self.pt1 + translate)
        except TypeError:
            return NotImplemented

    def __sub__(self, other: Sequence[float]) -> 'Line2':
        try:
            t = Vector2(other)
            return Line2(self.pt0 - t, self.pt1 - t)
        except TypeError:
            return NotImplemented

    def __repr__(self) -> str:
        return '{class_name}({pt0!s}, {pt1!s})' \
               .format(class_name=type(self).__name__, pt0=tuple(self.pt0), pt1=tuple(self.pt1))


def isiterable(x: Any) -> bool:
    try:
        iter(x)
    except TypeError:
        return False
    else:
        return True
