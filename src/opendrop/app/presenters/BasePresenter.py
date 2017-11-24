from abc import abstractmethod

from opendrop.app.views.BaseView import BaseView
from opendrop.app.presenters import handler, controlled_by

class BasePresenter:
    def __init__(self, model, view: BaseView):
        # make sure events are present
        pass

    def setup(self):
        pass

    def teardown(self):
        pass

    def can_control(self, view: BaseView):
        pass # figure it out

    def set_view(self, new_view: BaseView):
        pass


    def __del__(self):
        pass


    # example implementation

    # @handler("on_menu_select")
    # def handle_menu_select(self, id):
    #     self.change_view(views.PendantDropConfiguration) # change view by name.

@controlled_by(BasePresenter)  # convert class to abstract class as well with decorator
class Controllable:
    controlled_by = BasePresenter # hook the events as well
    @abstractmethod
    def set_menu_icon(self): pass









