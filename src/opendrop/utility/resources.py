from abc import abstractmethod

from typing import Type, Any, List, Set


class IResource:
    @abstractmethod
    def destroy(self) -> None: pass


class ResourceToken:
    def __init__(self, resource_cls: Type[IResource]) -> None:
        self._resource_cls = resource_cls  # type: Type[IResource]

        self._instance = None  # type: IResource
        self._references = 0  # type: int

        self._wrapper = self._create_resource_wrapper(resource_cls)  # type: type

    def acquire(self) -> IResource:
        if not self._instance:
            self._instance = self._resource_cls()

        self._references += 1

        return self._wrapper(self._instance)

    def _release(self) -> None:
        self._references -= 1

        if self._references == 0:
            self._instance.destroy()
            self._instance = None

    def _create_resource_wrapper(self, resource_cls: Type[IResource]) -> type:
        resource_metacls = type(resource_cls)

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

            def __str__(self):
                return str(resource_cls)

        class ResourceWrapper(resource_cls, metaclass=ResourceWrapperMeta):
            LOCALS = {'_target', 'token', 'release', 'released'}  # type: Set[str]

            token = self  # type: ResourceToken

            def __init__(self, target: IResource) -> None:
                self._target = target  # type: IResource
                self.released = False  # type: bool

            def __getattribute__(self, name: str) -> Any:
                if name in ResourceWrapper.LOCALS:
                    return object.__getattribute__(self, name)
                else:
                    return getattr(self._target, name)

            def __setattr__(self, name: str, value: Any) -> None:
                if name in ResourceWrapper.LOCALS:
                    object.__setattr__(self, name, value)
                else:
                    setattr(self._target, name, value)

            def release(self) -> None:
                if self.released:
                    raise ValueError('Resource has already been released.')

                self.released = True

                self.token._release()

        return ResourceWrapper
