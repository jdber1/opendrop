"""
How to use:

The @strategy decorator wraps a method to be used as a strategy. The method wrapped becomes the default implementation
of the strategy when none is chosen.

>>> class MyClass:
...    @strategy
...    def my_method(self):
...        return 0
...
>>> MyClass().my_method()
0

To choose a different implementation during runtime, call the `use()` method on the strategy:

>>> def my_method_impl(self):
...    return 1
...
>>> my_obj = MyClass()
>>> my_obj.my_method()
0
>>> my_obj.my_method.use(my_method_impl)
>>> my_obj.my_method()
1

To reset the implementation to the default, call `clear()`:

>>> my_obj.my_method.clear()
>>> my_obj.my_method()
0

Choosing an implementation is done independently for each instance:

>>> my_obj1 = MyClass()
>>> my_obj2 = MyClass()
>>> my_obj1.my_method.use(my_method_impl)
>>> my_obj1.my_method(), my_obj2.my_method()
(1, 0)

>>> my_obj.my_method()

@strategy also works with @classmethod and @staticmethod.

>>> class MyClass:
...    @strategy
...    def my_method(self):
...        return 0
...
...     @strategy
...     @classmethod
...     def my_class_method(cls):
...         return cls
...
...     @strategy
...     @staticmethod
...     def my_static_method(param):
...         return param
...
>>> MyClass.my_class_method() == MyClass().my_class_method() == MyClass
True
>>> MyClass.my_static_method(15) == MyClass().my_static_method(15) == 15
True

When choosing an implementation for a class like so:

>>> MyClass.my_method.use(my_method_impl)

This will modify the default implementation of all instances (regardless if they were instantiated before or after
`use()` was called), example:

>>> def my_method_impl2(self):
...     return 2
...
>>> MyClass.my_method.use(my_method_impl)
>>> my_obj = MyClass()
>>> my_obj.my_method()
1
>>> my_obj.my_method.clear(); my_obj.my_method()
1
>>> my_obj.my_method.use(my_method_impl2); my_obj.my_method()
2
>>> my_obj.my_method.clear(); my_obj.my_method()
1

Choosing an implementation for a class will also affect the default implementation for subclasses and instances of those
subclasses:

>>> class MyClass:
...     @strategy
...     def my_method(self=None):
...         return 0
...
>>> class MySubclass(MyClass):
...     pass
...
>>> MyClass.my_method.use(my_method_impl)
>>> MyClass.my_method(), MySubclass.my_method(), MySubclass().my_method()
(1, 1, 1)

However, in the following example;

>>> class MyClass:
...     @strategy
...     def my_method(self=None):
...         return 0
...
>>> class MySubclass(MyClass):
...     @strategy
...     def my_method(self=None):
...         return 10
...
>>> MyClass.my_method.use(my_method_impl)
>>> MyClass.my_method(), MySubclass.my_method(), MySubclass().my_method()
(1, 10, 10)

The `my_method` strategy has been redefined in `MySubclass` and so overrides the original strategy in `MyClass`, thus
`MyClass.my_method` and `MySubclass.my_method` no longer refer to the same strategy.

In general, the implementation of a strategy chosen is done as follows:

Check if instance has a custom implementation, else
Check if class of instance has a custom implementation, else
Check if superclasses have a custom implementation (following MRO), else
Use the default implementation that was decorated with @strategy

Information about what implementation has been chosen for each instance/class is stored as an attribute with the format
_strategyXXXX, where XXXX is some numerical ID to avoid naming collision. As such, the instances and classes that use
@strategy must have the ability to add new attributes.
"""

import inspect
from abc import abstractmethod
from typing import Callable, Optional, Any, Tuple

STRATEGY_HIDDEN_ATTR_NAME_FORMAT = '_strategy{}'  # type: str


class Strategy:
    def __init__(self, descriptor_args: Optional[Tuple[Any, Any]],
                 extra_decorator: Callable[[Callable], Callable] = None) -> None:
        self._extra_decorator = extra_decorator  # type: Callable
        self._descriptor_args = descriptor_args  # type: Tuple[Any, Any]

    def __call__(self, *args, **kwargs) -> Any:
        f = self._do_descriptor_protocol(self._get_impl())  # type: Callable

        return f(*args, **kwargs)

    def use(self, f: Callable) -> None:
        f_decorated = self._extra_decorator(f) if self._extra_decorator is not None else f  # type: Callable

        f_decorated_sig = inspect.signature(self._do_descriptor_protocol(f_decorated))  # type: inspect.Signature

        if not self._check_signature_compatible(f_decorated_sig):
            raise ValueError

        self._use_impl(f_decorated)

    def clear(self) -> None:
        self._use_impl(None)

    def _do_descriptor_protocol(self, f: Callable) -> Callable:
        if self._descriptor_args is not None and hasattr(f, '__get__'):
            f = f.__get__(*self._descriptor_args)

        return f

    def _check_signature_compatible(self, f_sig: inspect.Signature) -> bool:
        # Signature checking of strategy implementation not yet implemented, so any strategy may use any
        # implementation, even if signatures are incompatible, e.g.
        #
        #     @strategy
        #     def test(a):
        #         pass
        #
        #     def impl(a, b, c):
        #         return a + b + c
        #
        #     test.use(impl)  # Currently works
        #
        # TODO: Implement this
        # A signature is compatible if the function decorated by @strategy can be safely replaced with the
        # implementation, so any valid calls that can be made to the original function also works with the new
        # implementation.

        my_sig = inspect.signature(self._do_descriptor_protocol(self._get_impl()))  # type: inspect.Signature

        return True

    @abstractmethod
    def _get_impl(self) -> Callable: pass

    @abstractmethod
    def _use_impl(self, value: Optional[Callable]) -> None: pass


class UnboundStrategy:
    def __init__(self, default: Callable):
        self._extra_decorator = None  # type: Callable

        if isinstance(default, classmethod):
            self._extra_decorator = classmethod
        elif isinstance(default, staticmethod):
            self._extra_decorator = staticmethod

        self._default = default  # type: Callable

    def __get__(self, instance: Any, owner: type):
        if instance is None:
            if self._hidden_attr_name not in owner.__dict__:
                setattr(owner, self._hidden_attr_name,
                        ClassStrategy(
                            unbound=self,
                            owner=owner,
                            extra_decorator=self._extra_decorator
                        ))

            return getattr(owner, self._hidden_attr_name)
        else:
            if self._hidden_attr_name not in instance.__dict__:
                setattr(instance, self._hidden_attr_name,
                        InstanceStrategy(
                            cls_bound=self.__get__(None, owner),
                            instance=instance,
                            extra_decorator=self._extra_decorator
                        ))

            return getattr(instance, self._hidden_attr_name)

    @property
    def _hidden_attr_name(self):
        return STRATEGY_HIDDEN_ATTR_NAME_FORMAT.format(id(self))


class ClassStrategy(Strategy):
    def __init__(self, unbound: UnboundStrategy, owner: type, extra_decorator: Optional[Callable]) -> None:
        super().__init__((None, owner), extra_decorator)

        self._unbound = unbound  # type: UnboundStrategy

        self._owner = owner  # type: type

        self._override = None  # type: Optional[Callable]

    def _get_impl(self) -> Callable:
        super_owner = super(self._owner, self._owner)

        super_strategy = getattr(super_owner, self._unbound._hidden_attr_name, None)  # type: Optional[Strategy]

        impl = self._unbound._default  # type: Callable

        if self._override is not None:
            impl = self._override
        elif super_strategy is not None:
            impl = super_strategy._get_impl()

        return impl

    def _use_impl(self, value: Optional[Callable]) -> None:
        self._override = value


class InstanceStrategy(Strategy):
    def __init__(self, cls_bound: ClassStrategy, instance: Any, extra_decorator: Optional[Callable]) -> None:
        super().__init__((instance, type(instance)), extra_decorator)

        self._cls_bound = cls_bound  # type: UnboundStrategy

        self._override = None  # type: Optional[Callable]

    def _get_impl(self) -> Callable:
        if self._override is not None:
            impl = self._override  # type: Callable
        else:
            impl = self._cls_bound._get_impl()  # type: Callable

        return impl

    def _use_impl(self, value: Optional[Callable]) -> None:
        self._override = value


def strategy(f: Callable) -> UnboundStrategy:
    return UnboundStrategy(f)
