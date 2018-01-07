from typing import List, Type, Mapping

from opendrop.mvp.IView import IView
from opendrop.mvp.Presenter import Presenter


# No longer used, pending removal.
class ViewPresenterMap:

    """Helper container class that stores a list of views and presenters, and can be used to get the view class for a
    presented by a given presenter, or the presenter class that presents a given view.
    """

    def __init__(self, views: List[Type[IView]], presenters: List[Type[Presenter]]) -> None:
        """Initialise the map with a given list of views and presenters.
        :param views: The list of views
        :param presenters: The list of presenters
        """
        self._view_to_presenters = {
            view_cls: self._find_presenter_for_view(view_cls, presenters)
            for view_cls in views
        }  # type: Mapping[Type[IView], Type[Presenter]]

    def presenter_from_view(self, view_cls: Type[IView]) -> Type[Presenter]:
        """Return the presenter that presents `view_cls`
        :param view_cls: The view class to find the matching presenter
        :return: The presenter that presents `view_cls`
        """
        return self._view_to_presenters[view_cls]

    def view_from_presenter(self, presenter_cls: Type[Presenter]) -> Type[IView]:
        """Return the view that is presented by `presenter_cls`
        :param presenter_cls: The presenter class to find the matching view
        :return: The view that is presented by `presenter_cls`
        """
        for view_cls, searched_presenter_cls in self._view_to_presenters.items():
            if presenter_cls == searched_presenter_cls:
                return view_cls

    # With the current implementation, views and presenters are stored in a dictionary with each view being the key to
    # their presenter. This helper method finds the presenter from a list of presenters that presents the given view.
    @staticmethod
    def _find_presenter_for_view(view_cls: Type[IView], presenter_clses: List[Type[Presenter]]) -> Type[Presenter]:
        for presenter_cls in presenter_clses:
            if presenter_cls.can_control(view_cls):
                return presenter_cls
