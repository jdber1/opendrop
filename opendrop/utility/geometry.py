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


import math
import operator
from typing import Any, Callable, Iterable, Tuple, TypeVar, overload

from typing import Literal, Protocol


T_co = TypeVar('T_co', covariant=True)
U_co = TypeVar('U_co', covariant=True)

T_contra = TypeVar('T_contra', contravariant=True)


class SupportsAdd(Protocol[T_contra, U_co]):
    def __add__(self, other: T_contra) -> U_co: ...


class SupportsRAdd(Protocol[T_contra, U_co]):
    def __radd__(self, other: T_contra) -> U_co: ...


class SupportsMul(Protocol[T_contra, U_co]):
    def __mul__(self, other: T_contra) -> U_co: ...


class SupportsRMul(Protocol[T_contra, U_co]):
    def __rmul__(self, other: T_contra) -> U_co: ...


class SupportsSub(Protocol[T_contra, U_co]):
    def __sub__(self, other: T_contra) -> U_co: ...


class SupportsRSub(Protocol[T_contra, U_co]):
    def __rsub__(self, other: T_contra) -> U_co: ...


class SupportsTrueDiv(Protocol[T_contra, U_co]):
    def __truediv__(self, other: T_contra) -> U_co: ...


class SupportsRTrueDiv(Protocol[T_contra, U_co]):
    def __rtruediv__(self, other: T_contra) -> U_co: ...


class SupportsFloorDiv(Protocol[T_contra, U_co]):
    def __floordiv__(self, other: T_contra) -> U_co: ...


class SupportsRFloorDiv(Protocol[T_contra, U_co]):
    def __rfloordiv__(self, other: T_contra) -> U_co: ...


class SupportsNeg(Protocol[T_co]):
    def __neg__(self) -> T_co: ...


class SupportsPos(Protocol[T_co]):
    def __pos__(self) -> T_co: ...


class Comparable(Protocol[T_contra]):
    def __lt__(self, other: T_contra) -> bool: ...

    def __gt__(self, other: T_contra) -> bool: ...

    def __le__(self, other: T_contra) -> bool: ...

    def __ge__(self, other: T_contra) -> bool: ...


class Number(
        SupportsAdd,
        SupportsSub,
        SupportsMul,
        SupportsTrueDiv,
        SupportsNeg,
        SupportsPos,
        Comparable,
        Protocol,
):
    ...


NumberT_co = TypeVar('NumberT_co', bound=Number, covariant=True)
NumberU = TypeVar('NumberU', bound=Number)
NumberV = TypeVar('NumberV', bound=Number)


class _PlainVector2(Tuple[T_co, T_co]):
    def __getitem__(self, index: Literal[0, 1]) -> T_co:
        return super().__getitem__(index)

    @property
    def x(self) -> T_co:
        return self[0]

    @property
    def y(self) -> T_co:
        return self[1]

    def __len__(self) -> Literal[2]:
        return 2


class Vector2(_PlainVector2[NumberT_co]):
    @overload
    def __new__(cls, x: NumberT_co, y: NumberT_co) -> 'Vector2[NumberT_co]': ...
    @overload
    def __new__(cls, iterable: Iterable[NumberT_co]) -> 'Vector2[NumberT_co]': ...

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
                    'No {} constructor found for arguments {} and keyword arguments {}'
                    .format(cls.__name__, args, kwargs)
            )

    @classmethod
    def _from_xy(cls, x: NumberT_co, y: NumberT_co) -> 'Vector2[NumberT_co]':
        return super().__new__(cls, (x, y))

    @classmethod
    def _from_iterable(cls, iterable: Iterable[NumberT_co]) -> 'Vector2[NumberT_co]':
        x, y = iterable
        return cls._from_xy(x, y)

    def replace(self: 'Vector2[NumberU]', **kwargs: NumberU) -> 'Vector2[NumberU]':
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

    def map(self, func: Callable[[NumberT_co], NumberU]) -> 'Vector2[NumberU]':
        return Vector2(map(func, self))

    def __neg__(self: _PlainVector2[SupportsNeg[NumberU]]) -> 'Vector2[NumberU]':
        try:
            return Vector2(map(operator.neg, self))
        except TypeError:
            return NotImplemented

    def __pos__(self: _PlainVector2[SupportsPos[NumberU]]) -> 'Vector2[NumberU]':
        try:
            return Vector2(map(operator.pos, self))
        except TypeError:
            return NotImplemented

    @overload
    def __add__(self: _PlainVector2[SupportsAdd[NumberU, NumberV]], other: Iterable[NumberU]) -> 'Vector2[NumberV]': ...
    @overload
    def __add__(self, other: Iterable[SupportsRAdd[NumberT_co, NumberU]]) -> 'Vector2[NumberU]': ...

    def __add__(self, other):
        try:
            return Vector2(map(operator.add, self, other))
        except TypeError:
            return NotImplemented

    @overload
    def __radd__(self: _PlainVector2[SupportsRAdd[NumberU, NumberV]], other: Iterable[NumberU]) -> 'Vector2[NumberV]': ...
    @overload
    def __radd__(self, other: Iterable[SupportsAdd[NumberT_co, NumberU]]) -> 'Vector2[NumberU]': ...

    def __radd__(self, other):
        try:
            return Vector2(map(operator.add, other, self))
        except TypeError:
            return NotImplemented

    @overload
    def __sub__(self: _PlainVector2[SupportsSub[NumberU, NumberV]], other: Iterable[NumberU]) -> 'Vector2[NumberV]': ...
    @overload
    def __sub__(self, other: Iterable[SupportsRSub[NumberT_co, NumberU]]) -> 'Vector2[NumberU]': ...

    def __sub__(self, other):
        try:
            return Vector2(map(operator.sub, self, other))
        except TypeError:
            return NotImplemented

    @overload
    def __rsub__(self: _PlainVector2[SupportsRSub[NumberU, NumberV]], other: Iterable[NumberU]) -> 'Vector2[NumberV]': ...
    @overload
    def __rsub__(self, other: Iterable[SupportsSub[NumberT_co, NumberU]]) -> 'Vector2[NumberU]': ...

    def __rsub__(self, other):
        try:
            return Vector2(map(operator.sub, other, self))
        except TypeError:
            return NotImplemented

    @overload
    def __mul__(self: _PlainVector2[SupportsMul[NumberU, NumberV]], other: NumberU) -> 'Vector2[NumberV]': ...

    @overload
    def __mul__(self, other: SupportsRMul[NumberT_co, NumberU]) -> 'Vector2[NumberU]': ...

    @overload
    def __mul__(self: _PlainVector2[SupportsMul[NumberU, NumberV]], other: Iterable[NumberU]) -> 'Vector2[NumberV]': ...

    @overload
    def __mul__(self, other: Iterable[SupportsRMul[NumberT_co, NumberU]]) -> 'Vector2[NumberU]': ...

    def __mul__(self, other):
        try:
            if isiterable(other):
                return self._elementwise_mul(other)
            else:
                return Vector2(x*other for x in self)
        except TypeError:
            return NotImplemented

    def _elementwise_mul(self: _PlainVector2[SupportsMul[NumberU, NumberV]], other: Iterable[NumberU]) -> 'Vector2[NumberV]':
        return Vector2(map(operator.mul, self, other))

    @overload
    def __rmul__(self: _PlainVector2[SupportsRMul[NumberU, NumberV]], other: NumberU) -> 'Vector2[NumberV]': ...

    @overload
    def __rmul__(self, other: SupportsMul[NumberT_co, NumberU]) -> 'Vector2[NumberU]': ...

    @overload
    def __rmul__(self: _PlainVector2[SupportsRMul[NumberU, NumberV]], other: Iterable[NumberU]) -> 'Vector2[NumberV]': ...

    @overload
    def __rmul__(self, other: Iterable[SupportsMul[NumberT_co, NumberU]]) -> 'Vector2[NumberU]': ...

    def __rmul__(self, other):
        try:
            if isiterable(other):
                return self._elementwise_rmul(other)
            else:
                return Vector2(other*x for x in self)
        except TypeError:
            return NotImplemented

    def _elementwise_rmul(self: _PlainVector2[SupportsRMul[NumberU, NumberV]], other: Iterable[NumberU]) -> 'Vector2[NumberV]':
        return Vector2(map(operator.mul, other, self))

    @overload
    def __truediv__(self: _PlainVector2[SupportsTrueDiv[NumberU, NumberV]], other: NumberU) -> 'Vector2[NumberV]': ...
    @overload
    def __truediv__(self, other: SupportsRTrueDiv[NumberT_co, NumberU]) -> 'Vector2[NumberU]': ...

    def __truediv__(self, other):
        try:
            return Vector2(x/other for x in self)
        except TypeError:
            return NotImplemented

    @overload
    def __floordiv__(self: _PlainVector2[SupportsFloorDiv[NumberU, NumberV]], other: NumberU) -> 'Vector2[NumberV]': ...
    @overload
    def __floordiv__(self, other: SupportsRFloorDiv[NumberT_co, NumberU]) -> 'Vector2[NumberU]': ...

    def __floordiv__(self, other):
        try:
            return Vector2(x//other for x in self)
        except TypeError:
            return NotImplemented

    def __repr__(self) -> str:
        return '{class_name}({x}, {y})'.format(
                class_name=type(self).__name__,
                x=self[0],
                y=self[1],
        )


class _PlainRect2(Tuple[T_co, T_co, T_co, T_co]):
    def __getitem__(self, index: Literal[0, 1, 2, 3]) -> T_co:
        return super().__getitem__(index)
    
    @property
    def x0(self) -> T_co:
        return self[0]
    
    @property
    def y0(self) -> T_co:
        return self[1]
    
    @property
    def x1(self) -> T_co:
        return self[2]
    
    @property
    def y1(self) -> T_co:
        return self[3]

    def __len__(self) -> Literal[4]:
        return 4
 

class Rect2(_PlainRect2[NumberT_co]):
    @overload
    def __new__(cls, iterable: Iterable[NumberT_co]) -> 'Rect2[NumberT_co]': ...
    @overload
    def __new__(cls, x0: NumberT_co, y0: NumberT_co, x1: NumberT_co, y1: NumberT_co) -> 'Rect2[NumberT_co]': ...
    @overload
    def __new__(cls, pt0: Iterable[NumberT_co], pt1: Iterable[NumberT_co]) -> 'Rect2[NumberT_co]': ...
    @overload
    def __new__(cls, *, x: NumberT_co, y: NumberT_co, w: NumberT_co, h: NumberT_co) -> 'Rect2[NumberT_co]': ...
    @overload
    def __new__(cls, *, position: Iterable[NumberT_co], size: Iterable[NumberT_co]) -> 'Rect2[NumberT_co]': ...
     
    def __new__(cls, *args, **kwargs):
        if len(args) == 1:
            return cls._from_iterable(*args)
        elif len(args) == 4:
            return cls._from_x0y0x1y1(*args)
        elif len(args) == 2:
            return cls._from_pt0pt1(*args)
        elif 'x0' in kwargs:
            return cls._from_x0y0x1y1(**kwargs)
        elif 'x' in kwargs:
            return cls._from_xywh(**kwargs)
        elif 'pt0' in kwargs:
            return cls._from_pt0pt1(**kwargs)
        elif 'position' in kwargs:
            return cls._from_position_and_size(**kwargs)
        else:
            raise TypeError(
                    'No {} constructor found for arguments {} and keyword arguments {}'
                    .format(cls.__name__, args, kwargs)
            )

    @classmethod
    def _from_x0y0x1y1(cls, x0: NumberT_co, y0: NumberT_co, x1: NumberT_co, y1: NumberT_co) -> 'Rect2[NumberT_co]':
        if x0 > x1:
            x0, x1 = x1, x0
 
        if y0 > y1:
            y0, y1 = y1, y0

        return super().__new__(cls, (x0, y0, x1, y1))

    @classmethod
    def _from_pt0pt1(cls, pt0: Iterable[NumberT_co], pt1: Iterable[NumberT_co]) -> 'Rect2[NumberT_co]':
        x0, y0 = pt0
        x1, y1 = pt1
        return cls._from_x0y0x1y1(x0, y0, x1, y1)

    @classmethod
    def _from_xywh(cls, x: NumberT_co, y: NumberT_co, w: NumberT_co, h: NumberT_co) -> 'Rect2[NumberT_co]':
        x0, y0 = x, y
        x1, y1 = x+w, y+h
        return cls._from_x0y0x1y1(x0, y0, x1, y1)

    @classmethod
    def _from_position_and_size(cls, position: Iterable[NumberT_co], size: Iterable[NumberT_co]) -> 'Rect2[NumberT_co]':
        x, y = position
        w, h = size
        return cls._from_xywh(x, y, w, h)

    @classmethod
    def _from_iterable(cls, iterable: Iterable[NumberT_co]) -> 'Rect2[NumberT_co]':
        x0, y0, x1, y1 = iterable
        return cls._from_x0y0x1y1(x0, y0, x1, y1)
 
    @property
    def pt0(self) -> Vector2[NumberT_co]:
        return Vector2(self.x0, self.y0)

    @property
    def pt1(self) -> Vector2[NumberT_co]:
        return Vector2(self.x1, self.y1)

    @property
    def x(self) -> NumberT_co:
        return self.x0

    @property
    def y(self) -> NumberT_co:
        return self.y0

    @property
    def w(self) -> NumberT_co:
        return self.x1 - self.x0

    @property
    def h(self) -> NumberT_co:
        return self.y1 - self.y0

    @property
    def position(self) -> Vector2[NumberT_co]:
        return Vector2(self.x, self.y)

    @property
    def size(self) -> Vector2[NumberT_co]:
        return Vector2(self.w, self.h)

    def replace(self: 'Rect2[NumberU]', **kwargs: NumberU) -> 'Rect2[NumberU]':
        raise NotImplementedError

    def map(self, func: Callable[[NumberT_co], NumberU]) -> 'Rect2[NumberU]':
        return Rect2(map(func, self))

    def __repr__(self) -> str:
        return '{class_name}(x0={x0}, y0={y0}, x1={x1}, y1={y1})' \
               .format(class_name=type(self).__name__, x0=self.x0, y0=self.y0, x1=self.x1, y1=self.y1)
 
    @overload
    def contains(self: _PlainRect2[Comparable[NumberU]], point: Iterable[NumberU], include_boundary: bool = True) -> bool: ...
    @overload
    def contains(self, point: Iterable[Comparable[NumberT_co]], include_boundary: bool = True) -> bool: ...
    
    def contains(self, point, include_boundary=True):
        point_vec = Vector2(point)
        if include_boundary:
            return self.x0 <= point_vec.x <= self.x1 and self.y0 <= point_vec.y <= self.y1
        else:
            return self.x0 < point_vec.x < self.x1 and self.y0 < point_vec.y < self.y1
 
    @overload
    def intersects(self: _PlainRect2[Comparable[NumberU]], other: Iterable[NumberU]) -> bool: ...
    @overload
    def intersects(self, other: Iterable[Comparable[NumberT_co]]) -> bool: ...

    def intersects(self, other):
        """Return True if this Rect2 is intersecting with the `other` Rect2. Return False if they do not
        intersect or if they are only 'touching' (i.e. share edges)."""
        other = Rect2(other)
        return self.x1 > other.x0 and self.x0 < other.x1 and self.y1 > other.y0 and self.y0 < other.y1
 
 
class Line2:
    def __init__(self, pt0: Iterable[float], pt1: Iterable[float]) -> None:
        pt0_vec = Vector2(pt0)
        pt1_vec = Vector2(pt1)

        if pt1_vec.x < pt0_vec.x:
            pt1_vec, pt0_vec = pt0_vec, pt1_vec

        self._pt0 = pt0_vec  # Left point
        self._pt1 = pt1_vec  # Right point

    @property
    def pt0(self) -> Vector2[float]:
        return self._pt0

    @property
    def pt1(self) -> Vector2[float]:
        return self._pt1

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


def isiterable(x: Any) -> bool:
    try:
        iter(x)
    except TypeError:
        return False
    else:
        return True
