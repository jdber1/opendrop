def isfield(x):
    return all(hasattr(x, attr) for attr in [
        "__add__",
        "__mul__",
        "__neg__",
        "__sub__",
        "__div__"
    ])

class Vector2(object):
    def __new__(cls, *args, **kwargs):
        if len(args) == 0 and len(kwargs) == 0:
            return cls._from_none()
        elif len(args) == 1 and len(kwargs) == 0:
            try:
                return cls._from_tuple((args[0][0], args[0][1]))
            except:
                pass
        elif len(args) == 2 and len(kwargs) == 0:
            return cls._from_pos_args(*args)
        elif len(args) == 0 and len(kwargs) == 2:
            if all(name in kwargs for name in ("x", "y")):
                return cls._from_x_y_kwarg(**kwargs)

        raise TypeError(
            "Could not find instantiator for Vector2 with signature ({0}{1})".format(
                ", ".join(type(arg).__name__ for arg in args),
                kwargs and ", " + ", ".join(k + "=" + type(v).__name__ for k, v in kwargs.items())
                        or ""
            )
        )

    def round_to_int(self):
        return Vector2(int(round(self.x)), int(round(self.y)))

    def to_tuple(self):
        return (self.x, self.y)

    def __repr__(self):
        return "({x}, {y})".format(x=self.x, y=self.y)

    # Operators

    def __add__(self, other):
        if isinstance(other, Vector2):
            return Vector2(self.x + other.x, self.y + other.y)
        else:
            try:
                return Vector2(self.x + other[0], self.y + other[1])
            except (IndexError, TypeError):
                try:
                    return Vector2(self.x + other, self.y + other)
                except TypeError:
                    raise TypeError(
                        "unsupported operand type(s) for +: '{0}' and '{1}'"
                        .format(type(self).__name__, type(other).__name__)
                    )

    def __mul__(self, other):
        try:
            return Vector2(self.x * other, self.y * other)
        except TypeError:
            raise TypeError(
                "unsupported operand type(s) for *: '{0}' and '{1}'"
                .format(type(self).__name__, type(other).__name__)
            )

    def __neg__(self):
        return Vector2(-self.x, -self.y)

    def __sub__(self, other):
        return self + (-other)

    def __div__(self, other):
        try:
            return Vector2(self.x / other, self.y / other)
        except TypeError:
            raise TypeError(
                "unsupported operand type(s) for /: '{0}' and '{1}'"
                .format(type(self).__name__, type(other).__name__)
            )

    def __eq__(self, other):
        if isinstance(other, Vector2):
            return self.x == other.x and self.y == other.y
        else:
            try:
                return self.x == other[0] and self.y == other[1]
            except:
                return False

    # Iterable magic methods

    def __getitem__(self, i):
        return self.to_tuple()[i]

    def __iter__(self):
        return self.to_tuple().__iter__()

    def __len__(self):
        return len(self.to_tuple())

    # Instantiators

    @classmethod
    def _from_tuple(cls, tup):
        self = super(Vector2, cls).__new__(cls)

        if not all(isfield(elm) for elm in tup):
            raise TypeError(
                "Vector2 elements must implement +, *, -, /"
            )

        self.x = tup[0]
        self.y = tup[1]

        return self

    @classmethod
    def _from_x_y_kwarg(cls, x, y):
        return cls._from_tuple((x, y))

    @classmethod
    def _from_pos_args(cls, x, y):
        return cls._from_tuple((x, y))

    @classmethod
    def _from_none(cls):
        return cls._from_tuple((0, 0))

class BBox2(object):
    def __new__(cls, *args, **kwargs):
        if len(args) == 0 and len(kwargs) == 0:
            return cls._from_none()
        elif len(args) == 1 and len(kwargs) == 0:
            try:
                return cls._from_4tuple((args[0], args[1], args[2], args[3]))
            except (IndexError, TypeError):
                pass
        elif len(args) == 2 and len(kwargs) == 0:
            try:
                return cls._from_2tuples((args[0][0], args[0][1]), (args[1][0], args[1][1]))
            except (IndexError, TypeError):
                pass
        elif len(args) == 4 and len(kwargs) == 0:
            return cls._from_4_pos_args(*args)
        elif len(args) == 0 and len(kwargs) == 4:
            if all(name in kwargs for name in ("x", "y", "w", "h")):
                return cls._from_x_y_w_h_kwargs(**kwargs)
            elif all(name in kwargs for name in ("x0", "y0", "x1", "y1")):
                return cls._from_x0_y0_x1_y1_kwargs(**kwargs)
        elif len(args) == 0 and len(kwargs) == 2:
            if all(name in kwargs for name in ("p0", "p1")):
                return cls._from_p0_p1_kwargs(**kwargs)
            elif all(name in kwargs for name in ("position", "size")):
                return cls._from_position_size_kwargs(**kwargs)

        raise TypeError(
            "Could not find instantiator for BBox2 with signature ({0}{1})".format(
                ", ".join(type(arg).__name__ for arg in args),
                kwargs and ", " + ", ".join(k + "=" + type(v).__name__ for k, v in kwargs.items())
                        or ""
            )
        )

    def round_to_int(self):
        return BBox2(self.p0.round_to_int(), self.p1.round_to_int())

    def to_4tuple(self):
        return (self.x0, self.y0, self.x1, self.y1)

    def to_2tuple(self):
        return (Vector2(self.x0, self.y0), Vector2(self.x1, self.y1))

    _instantiated = False
    def _normalise(self):
        if self._instantiated:
            x0, y0 = min(self.x0, self.x1), min(self.y0, self.y1)
            x1, y1 = max(self.x0, self.x1), max(self.y0, self.y1)

            object.__setattr__(self, "x0", x0)
            object.__setattr__(self, "x1", x1)
            object.__setattr__(self, "y0", y0)
            object.__setattr__(self, "y1", y1)

    def __repr__(self):
        return "({x0}, {y0}, {x1}, {y1})".format(x0=self.x0, y0=self.y0, x1=self.x1, y1=self.y1)

    # Attributes

    @property
    def x(self):
        return self.x0

    @x.setter
    def x(self, v):
        self.x0 = v

    @property
    def y(self):
        return self.y0

    @y.setter
    def y(self, v):
        self.y0 = v

    @property
    def w(self):
        return self.x1 - self.x0

    @w.setter
    def w(self, v):
        self.x1 = self.x0 + v

    @property
    def h(self):
        return self.y1 - self.y0

    @h.setter
    def h(self, v):
        self.y1 = self.y0 + v

    @property
    def p0(self):
        return self.to_2tuple()[0]

    @p0.setter
    def p0(self, v):
        try:
            self.x0, self.y0 = v
        except (TypeError, ValueError):
            raise TypeError(
                "p0 must be a length 2 iterable"
            )

    @property
    def p1(self):
        return self.to_2tuple()[1]

    @p1.setter
    def p1(self, v):
        try:
            self.x1, self.y1 = v
        except (TypeError, ValueError):
            raise TypeError(
                "p1 must be a length 2 iterable"
            )

    @property
    def position(self):
        return self.p0

    @position.setter
    def position(self, v):
        self.p0 = v

    @property
    def size(self):
        return self.p1 - self.p0

    @size.setter
    def size(self, v):
        p1 = self.p0 + v

        self.p1 = p1

    def __setattr__(self, name, v):
        object.__setattr__(self, name, v)
        self._normalise()

    # Iterable magic methods

    def __getitem__(self, i):
        return self.to_4tuple()[i]

    def __iter__(self):
        return self.to_4tuple().__iter__()

    def __len__(self):
        return len(self.to_4tuple())

    # Operators

    def __mul__(self, other):
        try:
            return BBox2(self.p0 * other, self.p1 * other)
        except TypeError:
            raise TypeError(
                "unsupported operand type(s) for *: '{0}' and '{1}'"
                .format(type(self).__name__, type(other).__name__)
            )

    def __div__(self, other):
        try:
            return BBox2(self.p0 / other, self.p1 / other)
        except TypeError:
            raise TypeError(
                "unsupported operand type(s) for /: '{0}' and '{1}'"
                .format(type(self).__name__, type(other).__name__)
            )

    # Instantiators

    @classmethod
    def _from_4tuple(cls, tup):
        self = super(BBox2, cls).__new__(cls)

        if not all(isfield(elm) for elm in tup):
            raise TypeError(
                "Vector2 elements must implement +, *, -, /"
            )

        self.x0 = tup[0]
        self.y0 = tup[1]
        self.x1 = tup[2]
        self.y1 = tup[3]

        self._instantiated = True
        self._normalise()

        return self

    @classmethod
    def _from_2tuples(cls, tup0, tup1):
        return cls._from_4tuple((tup0[0], tup0[1], tup1[0], tup1[1]))

    @classmethod
    def _from_4_pos_args(cls, x0, y0, x1, y1):
        return cls._from_4tuple((x0, y0, x1, y1))

    @classmethod
    def _from_x_y_w_h_kwargs(cls, x, y, w, h):
        x1, y1 = x + w, y + h
        return cls._from_4tuple((x, y, x1, y1))

    @classmethod
    def _from_x0_y0_x1_y1_kwargs(cls, x0, y0, x1, y1):
        return cls._from_4tuple((x0, y0, x1, y1))

    @classmethod
    def _from_position_size_kwargs(cls, position, size):
        p0 = position
        p1 = (position[0] + size[0], position[1] + size[1])

        return cls._from_2tuples(p0, p1)

    @classmethod
    def _from_p0_p1_kwargs(cls, p0, p1):
        return cls._from_2tuples(p0, p1)

    @classmethod
    def _from_none(cls):
        return cls._from_4tuple((0, 0, 0, 0))
