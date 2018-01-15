import inspect
import types
import weakref
from abc import abstractmethod
from typing import Callable, Optional, Any, Tuple, List


class Strategy:
    def __init__(self, decorator: Callable[[Callable], Callable], descriptor_args: Optional[Tuple[Any, Any]] = None)\
            -> None:
        self._decorator = decorator
        self._descriptor_args = descriptor_args

    def __call__(self, *args, **kwargs) -> Any:
        f = self._do_descriptor_protocol(self._get_impl())  # type: Callable
        return f(*args, **kwargs)

    def use(self, f: Callable) -> None:
        # Save a copy for error reporting
        original_f = f  # type: Callable

        if self._decorator is not None:
            f = self._decorator(f)

        f_sig = inspect.signature(self._do_descriptor_protocol(f))  # type: inspect.Signature

        if not self.check_signature_compatible(f_sig):
            raise ValueError

        self._set_impl(f)

    def clear(self) -> None:
        self._set_impl(None)

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
    def _set_impl(self, value: Optional[Callable]) -> None: pass


class UnboundStrategy(Strategy):
    def __init__(self, default: Callable):
        decorator = None

        if isinstance(default, classmethod):
            decorator = classmethod
        elif isinstance(default, staticmethod):
            decorator = staticmethod

        super().__init__(decorator)

        self._default = default  # type: Callable
        self._custom = None  # type: Optional[Callable]

    def __get__(self, instance: Any, owner: type):
        if instance is None:
            # Convert to a 'class strategy'
            self._descriptor_args = (None, owner)

            return self

        strategy_hidden_attr_name = '_strategy{}'.format(id(self))  # type: str

        if not hasattr(instance, strategy_hidden_attr_name):
            setattr(instance, strategy_hidden_attr_name, InstanceStrategy(self, instance))

        return getattr(instance, strategy_hidden_attr_name)

    def _get_impl(self) -> Callable:
        return self._custom if self._custom is not None else self._default

    def _set_impl(self, value: Optional[Callable]) -> None:
        self._custom = value


class InstanceStrategy(Strategy):
    def __init__(self, parent: Strategy, instance: Any):
        super().__init__(parent._decorator, (instance, type(instance)))

        self._parent = parent  # type: UnboundStrategy

        self._custom = None  # type: Optional[Callable]

    def _get_impl(self) -> Callable:
        return self._custom if self._custom is not None else self._parent._get_impl()

    def _set_impl(self, value: Optional[Callable]) -> None:
        self._custom = value


def strategy(f: Callable) -> Strategy:
    return UnboundStrategy(f)
