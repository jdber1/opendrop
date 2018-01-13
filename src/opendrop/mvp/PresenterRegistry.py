import inspect
from typing import List, Type, Union, Iterable

from opendrop.mvp.Presenter import Presenter
from opendrop.mvp.View import View


class PresenterRegistry:
    def __init__(self, presenters: Iterable[Type[Presenter]]) -> None:
        self._presenters = list(presenters)  # type: List[Presenter]

    def get_presenter_for_view(self, view: Union[View, Type[View]]):
        if not inspect.isclass(view):
            view = type(view)

        for p in self._presenters:
            if p.can_control(view):
                return p
