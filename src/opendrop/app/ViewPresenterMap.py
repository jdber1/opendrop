from typing import List, overload

from opendrop.app.presenters import BasePresenter
from opendrop.app.views.BaseView import BaseView


class ViewPresenterMap:
    @overload
    def __init__(self, views: module, presenters: module) -> None:
        # stores the views and presenters
        # make sure no ambiguities
        pass

    @overload
    def __init__(self, views: List[BaseView], presenters: List[BasePresenter]) -> None:
        # stores the views and presenters
        # make sure no ambiguities
        pass

    def __init__(self, views, presenters):
        pass

    def presenter_from_view(self, view: BaseView) -> BasePresenter:
        pass

    def view_from_presenter(self, presenter: BasePresenter) -> BaseView:
        pass