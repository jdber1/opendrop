import inspect

from typing import TypeVar, Any, Type

T = TypeVar('T')


def patch_instance(obj: Any, mixin: Type[T]) -> T:
    """
    A simple patch instance, copy methods and attributes from class `mixin` into the __dict__ of existing instance of
    another class, `obj`. Dunder methods are ignored and descriptors won't work (as they are copied into the __dict__
    of the target instance, and so won't be invoked during attribute access). If an attribute of `mixin` is a non-data
    descriptor (such as a function) then instead of copying it straight into the target instance's __dict__, the result
    of calling `__get__(obj, type(obj))` is used. Data descriptors are ignored.

    Methods and attributes of `mixin` are copied over to `obj` only if they differ to those defined in the class of
    `obj`, for example:

        >>> class MyClass:
        >>>     def do_this(self):
        >>>         return 0
        ...
        >>> class MyMixin(MyClass):
        >>>     def do_this2(self):
        >>>         return 1
        ...
        >>> my_obj = MyClass()
        >>> my_obj.do_this = lambda: 2
        >>> patch_instance(my_obj, MyMixin)
        >>> print(my_obj.do_this(), my_obj.do_this2())
        2 1

    In this example, although `do_this` and `do_this2` are methods of MyMixin, when `my_obj` is patched, only `do_this2`
    is copied over, despite `my_obj.do_this` being unequal to `MyMixin.do_this` (it is ignored because `MyMixin.do_this`
    compares equal to `MyClass.do_this`).

    :param obj: Target instance to receive new methods/attributes from mixin
    :param mixin: The class that defines thew new methods and attributes target instance should receive
    :return: The target instance
    """
    for attr_name in dir(mixin):
        # Ignore dunder methods
        if attr_name.startswith('__') and attr_name.endswith('__'):
            continue

        attr_value = inspect.getattr_static(mixin, attr_name)

        if hasattr(attr_value, '__set__'):
            continue

        if hasattr(type(obj), attr_name) and inspect.getattr_static(type(obj), attr_name) == attr_value:
            continue

        if hasattr(attr_value, '__get__'):
            attr_value = attr_value.__get__(obj, type(obj))

        print('Patching {}:'.format(attr_name), inspect.getattr_static(obj, attr_name, None), inspect.getattr_static(mixin, attr_name))
        setattr(obj, attr_name, attr_value)

    return obj
