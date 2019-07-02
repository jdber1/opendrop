# Module that contains type information of certain classes to avoid circular imports.


from typing import Optional, MutableMapping, TypeVar

from typing_extensions import Protocol

ComponentViewRepType = TypeVar('ComponentViewRepType')

T = TypeVar('T')


class ComponentFactory(Protocol[ComponentViewRepType]):
    def create(self, view_env: Optional[MutableMapping] = None, presenter_env: Optional[MutableMapping] = None) \
            -> 'Component[ComponentViewRepType]':
        pass

    def fork(self, **options) -> 'ComponentFactory[ComponentViewRepType]':
        pass


class Component(Protocol[ComponentViewRepType]):
    def destroy(self) -> None:
        pass
