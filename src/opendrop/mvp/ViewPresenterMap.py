from typing import List, Type, Mapping

from opendrop.mvp.IView import IView
from opendrop.mvp.Presenter import Presenter


class ViewPresenterMap:
    def __init__(self, views: List[Type[IView]], presenters: List[Type[Presenter]]) -> None:
        self._view_to_presenters = {
            view_cls: self._find_presenter_for_view(view_cls, presenters)
            for view_cls in views
        }  # type: Mapping[Type[IView], Type[Presenter]]

    def presenter_from_view(self, view_cls: Type[IView]) -> Type[Presenter]:
        return self._view_to_presenters[view_cls]

    def view_from_presenter(self, presenter_cls: Type[Presenter]) -> Type[IView]:
        for view_cls, searched_presenter_cls in self._view_to_presenters.items():
            if presenter_cls == searched_presenter_cls:
                return view_cls

    @staticmethod
    def _find_presenter_for_view(view_cls: Type[IView], presenter_clses: List[Type[Presenter]]) -> Type[Presenter]:
        for presenter_cls in presenter_clses:
            if presenter_cls.can_present(view_cls):
                return presenter_cls
