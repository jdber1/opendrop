import math
from numbers import Number
from typing import Generic, TypeVar, Tuple, Callable, Iterator, Any, overload, Iterable, Union

NumericType = TypeVar('NT', bound=Number)
SomeNumericType = TypeVar('SomeNumericType', bound=Number)


class Vector2(Generic[NumericType]):
    def __init__(self, x: NumericType, y: NumericType) -> None:
        self._x = x
        self._y = y

    @property
    def x(self) -> NumericType:
        return self._x

    @property
    def y(self) -> NumericType:
        return self._y

    def as_type(self, cast: Callable[[NumericType], SomeNumericType]) -> 'Vector2[SomeNumericType]':
        return Vector2(cast(self.x), cast(self.y))

    def __neg__(self) -> 'Vector2[NumericType]':
        return Vector2(-self.x, -self.y)

    def __add__(self, other: Iterable[SomeNumericType]) -> 'Vector2':
        try:
            other = self._ensure_vector2(other)
        except TypeError:
            return NotImplemented

        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Iterable[SomeNumericType]) -> 'Vector2':
        try:
            other = self._ensure_vector2(other)
        except TypeError:
            return NotImplemented

        return self + (-other)

    @classmethod
    def _ensure_vector2(cls, obj: Iterable[SomeNumericType]) -> 'Vector2[SomeNumericType]':
        if isinstance(obj, cls):
            return obj

        if not isinstance(obj, Iterable) or len(tuple(obj)) != 2:
            raise TypeError

        return Vector2(*obj)

    def __mul__(self, other: SomeNumericType) -> 'Vector2':
        if not isinstance(other, Number):
            return NotImplemented
        return Vector2(self.x * other, self.y * other)

    __rmul__ = __mul__

    def __truediv__(self, other: SomeNumericType) -> 'Vector2':
        if not isinstance(other, Number):
            return NotImplemented
        return Vector2(self.x / other, self.y / other)

    def __floordiv__(self, other: SomeNumericType) -> 'Vector2':
        if not isinstance(other, Number):
            return NotImplemented
        return Vector2(self.x // other, self.y // other)

    def __len__(self) -> int:
        return 2

    def __iter__(self) -> Iterator[NumericType]:
        return iter((self.x, self.y))

    def __getitem__(self, i: int):
        if i == 0:
            return self.x
        elif i == 1:
            return self.y
        else:
            raise IndexError

    def __repr__(self) -> str:
        return '{class_name}(x={self.x}, y={self.y})' \
               .format(class_name=type(self).__name__, self=self)

    def __eq__(self, other: Tuple[NumericType, NumericType]) -> bool:
        if not (isinstance(other, Vector2) or isinstance(other, tuple)):
            return False

        return self[0] == other[0] and self[1] == other[1]


Vector2Like = Union[Vector2[NumericType], Tuple[NumericType, NumericType]]


class Rect2(Generic[NumericType]):
    @overload
    def __init__(self, *, x0: NumericType, y0: NumericType, x1: NumericType, y1: NumericType): ...

    @overload
    def __init__(self, *, x: NumericType, y: NumericType, w: NumericType, h: NumericType): ...

    @overload
    def __init__(self, *, p0: Vector2Like[NumericType], p1: Vector2Like[NumericType]): ...

    @overload
    def __init__(self, *, pos: Vector2Like[NumericType], size: Vector2Like[NumericType]): ...

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
    def p0(self) -> Vector2[NumericType]:
        return Vector2(self.x0, self.y0)

    @property
    def p1(self) -> Vector2[NumericType]:
        return Vector2(self.x1, self.y1)

    @property
    def pos(self) -> Vector2[NumericType]:
        return self.p0

    @property
    def size(self) -> Vector2[NumericType]:
        return Vector2(self.w, self.h)

    def as_type(self, cast: Callable[[NumericType], SomeNumericType]) -> 'Rect2[SomeNumericType]':
        return Rect2(x0=cast(self.x0), y0=cast(self.y0), x1=cast(self.x1), y1=cast(self.y1))

    def __iter__(self) -> Iterator[NumericType]:
        return iter((self.x0, self.y0, self.x1, self.y1))

    def __repr__(self) -> str:
        return '{class_name}(x0={self.x0}, y0={self.y0}, x1={self.x1}, y1={self.y1})' \
               .format(class_name=type(self).__name__, self=self)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Rect2):
            return False

        return (self.p0 == other.p0) and (self.p1 == other.p1)

    def contains_point(self, point: Vector2Like, include_boundary: bool = True):
        point = Vector2(*point)
        if include_boundary and (self.x0 <= point.x <= self.x1 and self.y0 <= point.y <= self.y1):
            return True
        elif self.x0 < point.x < self.x1 and self.y0 < point.y < self.y1:
            return True

        return False

    def is_intersecting(self, other: 'Rect2') -> bool:
        """Return True if the region defined by this Rect2 is intersecting with the region defined by `other`.
        Return False if they do not intersect or if they are only 'touching' (i.e. share edges but do not intersect)."""
        if self.x1 > other.x0 and self.x0 < other.x1 and self.y1 > other.y0 and self.y0 < other.y1:
            return True
        else:
            return False


class Line2(Generic[NumericType]):
    def __init__(self, p0: Vector2[NumericType], p1: Vector2[NumericType]):
        if p1[0] < p0[0]:
            p1, p0 = p0, p1

        self._p0 = p0  # Left point
        self._p1 = p1  # Right point

    @property
    def p0(self) -> Vector2[NumericType]:
        return self._p0

    @property
    def p1(self) -> Vector2[NumericType]:
        return self._p1

    @property
    def gradient(self) -> float:
        dx = self._p1[0] - self._p0[0]
        dy = self._p1[1] - self._p0[1]

        if dx == 0:
            return math.copysign(dy, math.inf)

        return dy/dx

    @overload
    def eval_at(self, *, x: NumericType) -> Vector2[NumericType]:
        ...
    @overload
    def eval_at(self, *, y: NumericType) -> Vector2[NumericType]:
        ...
    def eval_at(self, **kwargs) -> Vector2[NumericType]:
        if 'x' in kwargs:
            return self._eval_at_x(kwargs['x'])
        elif 'y' in kwargs:
            return self._eval_at_y(kwargs['y'])

    def _eval_at_x(self, x: NumericType) -> Vector2[NumericType]:
        p0_to_x = x - self.p0[0]
        return Vector2(x, self.p0[1] + p0_to_x * self.gradient)

    def _eval_at_y(self, y: NumericType) -> Vector2[NumericType]:
        p0_to_y = y - self.p0[1]

        if self.gradient == 0:
            x = math.copysign(p0_to_y, math.inf)
        else:
            x = self.p0[0] + p0_to_y / self.gradient

        return Vector2(x, y)
