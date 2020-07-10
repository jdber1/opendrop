from typing import Any, Callable, Sequence, Type, TypeVar, Generic, overload

import injector

T = TypeVar('T')
U = TypeVar('U')

CallableT = TypeVar('CallableT', bound=Callable)


def injection_container(modules: Sequence = (), auto_bind: bool = True) -> Callable[[T], T]:
    def wrapper(class_like: T) -> T:
        mark_as_injection_container(class_like, modules, auto_bind)
        return class_like
    return wrapper


def mark_as_injection_container(class_like: Any, modules: Sequence = (), auto_bind: bool = True) -> None:
    container_spec = InjectionContainerSpec(modules, auto_bind)
    class_like.__injection_container__ = container_spec


class InjectionContainerSpec:
    def __init__(self, modules: Sequence, auto_bind: bool) -> None:
        self.modules = modules
        self.auto_bind = auto_bind


class InjectionContainerPrivate:
    private_key = '_injection_container_private_data'

    def __init__(self, injector: 'Injector') -> None:
        self.injector = injector
        self.cache = {}

    def install(self, target: Any) -> None:
        target.__dict__[__class__.private_key] = self

    @staticmethod
    def get(owner: Any) -> 'InjectionContainerPrivate':
        return owner.__dict__[__class__.private_key]


# Make our custom Injector compare equal to the actual injector.Injector so it can be used as an injection key
# to get a reference to the injector, i.e. (where Injector refers to our redefined Injector class)
#     injector = Injector()
#     @inject
#     def func(self: Injector):
#         assert self is injector
#     injector.call_with_injection(func)
class InjectorMeta(type):
    def __eq__(self, other) -> bool:
        return other == injector.Injector

    def __hash__(self) -> int:
        return hash(injector.Injector)


# Add extra code to Injector that deals with injection container creation.
class Injector(injector.Injector, metaclass=InjectorMeta):
    def create_object(self, cls: Type[T], additional_kwargs: Any = None) -> T:
        additional_kwargs = additional_kwargs or {}
        
        container_spec = getattr(cls, '__injection_container__', None)
        if container_spec is None:
            return super().create_object(cls, additional_kwargs)
        
        child_injector = Injector(
            modules=container_spec.modules,
            auto_bind=container_spec.auto_bind,
            parent=self
        )

        private = InjectionContainerPrivate(child_injector)

        instance = cls.__new__(cls, **additional_kwargs)
        private.install(instance)
        instance.__init__(**additional_kwargs)

        return instance


class Inject(Generic[T]):
    def __init__(self, interface: Type[T]) -> None:
        self._interface = interface

    @overload
    def __get__(self, instance) -> T: ...
    @overload
    def __get__(self: U, instance, owner) -> U: ...

    def __get__(self, instance, owner=None):
        if owner is None:
            return self

        priv = InjectionContainerPrivate.get(instance)
        
        if self not in priv.cache:
            priv.cache[self] = priv.injector.get(self._interface)

        return priv.cache[self]
