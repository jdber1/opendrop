from abc import abstractmethod

from typing import Any, Generic, List, Set, Type, TypeVar


class IResource:
    @abstractmethod
    def teardown(self) -> None: pass

    def release(self) -> None: pass


T = TypeVar('T', bound=IResource)


class ResourceToken(Generic[T]):
    def __init__(self, resource_cls: Type[T], **kwargs) -> None:
        self._resource_cls = resource_cls  # type: Type[T]

        self._init_kwargs = kwargs

        self._instance = None  # type: T
        self._references = 0  # type: int

        self._wrapper = self._create_resource_wrapper(resource_cls)  # type: Type[T]

    def acquire(self) -> T:
        if not self._instance:
            self._instance = self._resource_cls(**self._init_kwargs)

        self._references += 1

        return self._wrapper(self._instance)

    def _release(self) -> None:
        self._references -= 1

        if self._references == 0:
            self._instance.teardown()
            self._instance = None

    def _create_resource_wrapper(self, resource_cls: Type[T]) -> Type[T]:
        resource_metacls = type(resource_cls)  # type: Type[Type[T]]

        class ResourceWrapperMeta(resource_metacls):
            def __new__(cls, name: str, bases: List[type], dict_: dict, *args) -> type:
                return resource_metacls.__new__(cls, resource_cls.__name__, bases, dict_)

            def __eq__(self, other: Any, *args, **kwargs) -> bool:
                if other == resource_cls:
                    return True
                else:
                    return super().__eq__(other)

            def __hash__(self):
                return hash(resource_cls)

        class ResourceWrapper(resource_cls, metaclass=ResourceWrapperMeta):
            LOCALS = {'_target', 'token', 'teardown', 'release', 'released'}  # type: Set[str]

            token = self  # type: ResourceToken[T]

            def __init__(self, target: IResource) -> None:
                self._target = target  # type: T
                self.released = False  # type: bool

            def __getattribute__(self, name: str) -> Any:
                if name in ResourceWrapper.LOCALS:
                    return object.__getattribute__(self, name)

                return getattr(self._target, name)

            def __setattr__(self, name: str, value: Any) -> None:
                if name in ResourceWrapper.LOCALS:
                    object.__setattr__(self, name, value)

                setattr(self._target, name, value)

            def teardown(self) -> None:
                raise ValueError('Can\'t call `teardown()` on a ResourceWrapper, did you mean `release()`?')

            def release(self) -> None:
                if self.released:
                    raise ValueError('Resource has already been released.')

                self.released = True

                self.token._release()

            def __del__(self):
                # If the resource wrapper is about to be garbage collected and is not yet released, then automatically
                # release it.
                if not self.released:
                    self.release()

        return ResourceWrapper
