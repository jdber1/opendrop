from typing import TypeVar, Any, Type

T = TypeVar('T')


def patch_instance(obj: Any, mixin: Type[T]) -> T:
    """
    A simple patch instance, copy methods and attributes from class `mixin` into the __dict__ of existing instance of
    another class, `obj`. Dunder methods are ignored and descriptors won't work (as they are copied into the __dict__
    of the target instance, and so won't be invoked during attribute access). If an attribute of `mixin` is a non-data
    descriptor (such as a function) then instead of copying it straight into the target instance's __dict__, the result
    of calling `__get__(obj, type(obj))` is used. Data descriptors are ignored.

    :param obj: Target instance to receive new methods/attributes from mixin
    :param mixin: The class that defines thew new methods and attributes target instance should receive
    :return: The target instance
    """
    for attr_name in dir(mixin):
        # Ignore dunder methods
        if attr_name.startswith('__') and attr_name.endswith('__'):
            continue

        attr_value = getattr(mixin, attr_name)

        if hasattr(obj, attr_name) and getattr(obj, attr_name) == attr_value:
            continue

        if hasattr(attr_value, '__set__'):
            continue

        if hasattr(attr_value, '__get__'):
            attr_value = attr_value.__get__(obj, type(obj))

        setattr(obj, attr_name, attr_value)

    return obj
