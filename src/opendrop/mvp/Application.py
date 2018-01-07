from abc import abstractmethod
from typing import Type, List, Optional, Iterable, Mapping, Any, TypeVar, Union, Iterator, Callable

import functools

from opendrop.mvp.Model import Model
from opendrop.mvp.IView import IView
from opendrop.mvp.Presenter import Presenter
from opendrop.mvp.PresenterRegistry import PresenterRegistry
from opendrop.mvp.View import View
from opendrop.mvp.ViewPresenterMap import ViewPresenterMap
from opendrop.utility.misc import get_classes_in_modules, recursive_load

T = TypeVar('T', bound=IView)


class VPRegistry:
    def __init__(self) -> None:
        self._records = []  # type: List[VPRecord]

    def new_record(self, *args, **kwargs) -> 'VPRecord':
        record = VPRecord(*args, on_family_dead_cb=self.handle_record_family_dead, **kwargs)

        self._records.append(record)

        return record

    def get_record_by_view(self, view: IView) -> 'VPRecord':
        for record in self._records:
            if record.view == view:
                return record
            else:
                try:
                    return record.get_record_by_view(view)
                except ValueError:
                    pass
        else:
            raise ValueError('No record with view matching {!r} found'.format(view))

    def handle_record_family_dead(self, record: 'VPRecord') -> None:
        self._records.remove(record)

    def __len__(self) -> int:
        return len(self._records)

    def __iter__(self) -> Iterator:
        return iter(self._records)

    def __bool__(self) -> bool:
        return True


class VPRecord(VPRegistry):
    def __init__(self, view: IView, presenter: Presenter, model: Optional[Model] = None,
                 attached_to_parent: bool = False, parent: Optional['VPRecord'] = None,
                 on_family_dead_cb: Optional[Callable] = None) -> None:
        super().__init__()

        self.view = view  # type: IView
        self.presenter = presenter  # type: Presenter
        self.model = model  # type: Optional[Model]

        self.attached_to_parent = attached_to_parent  # type: bool

        self.view_cls = type(view)

        self.parent = parent  # type: Optional['VPRecord']

        self.on_family_dead_cb = on_family_dead_cb  # type: Optional[Callable]

        self._dead = False  # type: bool

    def new_record(self, *args, **kwargs) -> 'VPRecord':
        return super().new_record(*args, parent=self, **kwargs)

    def handle_record_family_dead(self, record: 'VPRecord'):
        super().handle_record_family_dead(record)

        self.check_if_family_dead()

    def check_if_family_dead(self) -> None:
        if self.family_dead and self.on_family_dead_cb:
            self.on_family_dead_cb(self)

    @property
    def dead(self) -> bool:
        return self._dead

    @dead.setter
    def dead(self, value: bool) -> bool:
        self._dead = value

        self.check_if_family_dead()

    @property
    def family_dead(self) -> bool:
        if not self.dead:
            return False

        for child in self:
            if not child.family_dead:
                return False

        return True


class Application:

    """Manages the lifecycle of views and presenters and acts as the base class of some GUI application utilising this
    MVP framework.

    Attributes:
        PRESENTERS_PKG  The package containing the presenter classes this application uses.
    """

    PRESENTERS_PKG = []  # type: List[Type[Presenter]]

    def __init__(self) -> None:
        self._presenters = PresenterRegistry(
            get_classes_in_modules(recursive_load(self.PRESENTERS_PKG), cls=Presenter)
        )  # type: PresenterRegistry

        self._vp_registry = VPRegistry()  # type: VPRegistry

    def initialise_view(self, view_cls: Type[IView], view_opts: Mapping[str, Any]) -> IView:
        """Initialises `view_cls`. Override this if your application needs to pass arguments to the view constructor
        or any other advanced initialisation process.
        :param view_cls: The view class to be initialised.
        :param view_opts: Keyword arguments to be passed to the view constructor
        :return: The initialised view object.
        """
        return view_cls(**view_opts)

    def run(self, *args, **kwargs) -> None:
        """Run the application. Override this to implement any procedures that should be executed when the application
        runs, such as starting the GUI library's main loop.
        :return: None
        """
        self.main()

    @abstractmethod
    def main(self, *args, **kwargs) -> None:
        # TODO: Add documentation
        pass

    def quit(self, *args, **kwargs) -> None:
        """Quit the application. Override this to perform any clean up tasks like ending a GUI library's main loop.
        :return: None
        """
        pass

    def close(self, view: IView) -> None:
        record = self._vp_registry.get_record_by_view(view)  # type: VPRecord

        for child_record in record:
            if child_record.attached_to_parent:
                child_record.view.close()

        record = self._vp_registry.get_record_by_view(view)  # type: VPRecord

        record.view.destroy()
        record.presenter.destroy()

        record.dead = True

        self._check_if_all_views_dead()

    def spawn(self, view_cls: Union[Type[T], int], model: Model = None, child: bool = False,
              view_opts: Optional[Mapping[str, Any]] = None, src_view: Optional[IView] = None) -> Optional[T]:
        parent_registry = self._vp_registry.get_record_by_view(src_view) if src_view is not None else self._vp_registry

        if view_cls == View.PREVIOUS and src_view is not None:
            if parent_registry.parent is None:
                return None

            view_cls = parent_registry.parent.view_cls

            model = parent_registry.parent.model

        view_opts = view_opts if view_opts is not None else {}

        view = self.initialise_view(view_cls, view_opts)  # type: T

        # Set up hooks for `view.close()` and `view.spawn()`
        view.close.use(functools.partial(self.close, view=view))
        view.spawn.use(functools.partial(self.spawn, src_view=view))

        view.do_setup()

        presenter_cls = self._get_presenter_for_view(view)  # type: Type[Presenter]

        # Create and wire up the presenter
        presenter = presenter_cls(model=model, view=view)

        parent_registry.new_record(
            view=view,
            presenter=presenter,
            model=model,
            attached_to_parent=child
        )

        presenter.do_setup()

        return view

    def _check_if_all_views_dead(self):
        if len(self._vp_registry) == 0:
            self.quit()

    def _get_presenter_for_view(self, view: Union[IView, Type[IView]]) -> Type[Presenter]:
        return self._presenters.get_presenter_for_view(view)
