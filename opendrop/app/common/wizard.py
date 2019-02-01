from abc import abstractmethod
from typing import Generic, TypeVar, Callable, Optional

from typing_extensions import Protocol, runtime

from opendrop.mytypes import Destroyable

PresenterType = TypeVar('PresenterType', bound=Destroyable)


@runtime
class Validatable(Protocol):
    @abstractmethod
    def validate(self) -> bool:
        pass


class WizardPageWrapperPresenter(Generic[PresenterType]):
    create_presenter = None  # type: Callable[..., PresenterType]

    def __init__(self, *args, **kwargs) -> None:
        self._args = args
        self._kwargs = kwargs

        self._presenter = None  # type: Optional[PresenterType]
        self._enabled = False

        self.__destroyed = False
        self.__cleanup_tasks = [self.leave, self._drop_ref_to_args]

    def _drop_ref_to_args(self) -> None:
        del self._args
        del self._kwargs

    def validate(self) -> bool:
        assert self._enabled
        if not isinstance(self._presenter, Validatable):
            return True

        return self._presenter.validate()

    def enter(self) -> None:
        if self._enabled or self.__destroyed:
            return

        self._presenter = self.create_presenter(*self._args, **self._kwargs)
        self._enabled = True

    def leave(self) -> None:
        if not self._enabled or self.__destroyed:
            return

        assert self._presenter is not None
        self._presenter.destroy()
        self._enabled = False

    def destroy(self) -> None:
        assert not self.__destroyed
        for f in self.__cleanup_tasks:
            f()
        self.__destroyed = True
