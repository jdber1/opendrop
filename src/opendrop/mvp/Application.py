from typing import Type, List

from opendrop.mvp.Model import Model
from opendrop.mvp.IView import IView
from opendrop.mvp.Presenter import Presenter
from opendrop.mvp.ViewPresenterMap import ViewPresenterMap


class Application:
    MODEL = None  # type: Type[Model]
    VIEWS = []  # type: List[Type[IView]]
    PRESENTERS = []  # type: List[Type[Presenter]]

    ENTRY_VIEW = None  # type: Type[IView]

    def __init__(self, *args, **kwargs) -> None:
        assert self.ENTRY_VIEW in self.VIEWS

        self._model = self.MODEL()

        self._VPMAP = ViewPresenterMap(views=self.VIEWS, presenters=self.PRESENTERS)  # type: ViewPresenterMap

        self._active_views = []  # type: List[IView]

    def initialise_view(self, view_cls: Type[IView]) -> IView:
        return view_cls()

    def run(self, *args, **kwargs) -> None:
        pass

    def quit(self) -> None:
        pass

    def _register_active_view(self, view: IView) -> None:
        self._active_views.append(view)

    def _deregister_active_view(self, view: IView) -> None:
        self._active_views.remove(view)

        if not self._active_views:
            self.quit()

    def _new_view(self, view_cls: Type[IView]) -> None:
        model = self._model  # type: Model
        view = self.initialise_view(view_cls)  # type: IView

        presenter_cls = self._presenter_from_view(view_cls)  # type: Type[Presenter]

        # Create and wire up the presenter
        presenter_cls(model, view)

        # Connect view events to application
        view.connect('on_close', self._handle_view_close, once=True)
        # view.connect('on_spawn', self.handle_view_spawn)  # Not implemented

        self._register_active_view(view)

    def _presenter_from_view(self, view_cls: Type[IView]) -> Type[Presenter]:
        return self._VPMAP.presenter_from_view(view_cls)

    def _handle_view_close(self, src_view: IView, next_view_cls: Type[IView]) -> None:
        if next_view_cls:
            self._new_view(next_view_cls)

        self._deregister_active_view(src_view)
        src_view.destroy()
