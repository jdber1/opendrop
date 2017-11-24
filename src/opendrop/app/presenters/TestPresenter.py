from abc import abstractmethod, ABCMeta

from typing import Mapping

from opendrop.app.presenters.BasePresenter import BasePresenter
from opendrop.app.views.BaseView import BaseView
from opendrop.app.presenters.metadata import handles, controlled_by
from opendrop.app.presenters import ITestView

class TestPresenter(BasePresenter[ITestView]):
    def __init__(self, model, view: IView):
        # make sure events are present
        pass

    def setup(self):
        pass

    def teardown(self):
        pass

    def set_view(self, new_view: BaseView):
        pass

    def __del__(self):
        pass

    @handles('on_menu_select')
    def handle_menu_select(self, id):
        self.change_view(views.PendantDropConfiguration) # change view by name.



class TestView(ITestView):
    def blah(self):
        self.fire('on_menu_select', 1, 2, 3)








