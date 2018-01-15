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

        if not self.check_signature_compatible(f_decorated_sig):
            raise ValueError

        self._use_impl(f_decorated)

    def clear(self) -> None:
        self._use_impl(None)

    def _do_descriptor_protocol(self, f: Callable) -> Callable:
        if self._descriptor_args is not None and hasattr(f, '__get__'):
            f = f.__get__(*self._descriptor_args)

        return f

    def check_signature_compatible(self, f_sig: inspect.Signature) -> bool:
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
