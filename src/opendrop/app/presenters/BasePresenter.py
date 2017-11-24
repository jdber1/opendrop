from opendrop.app.views.BaseView import BaseView


# TODO: make use of generics for the type of view
class BasePresenter:
    view = None  # type: BaseView

    def __init__(self, model, view):
        # make sure events are present
        pass

    # def setup(self):
    #     pass
    #
    # def teardown(self):
    #     pass
    #
    # def can_control(self, view: BaseView):
    #     pass # figure it out
    #
    # def set_view(self, new_view: BaseView):
    #     pass
    #
    #
    #
    # def __del__(self):
        pass


    # example implementation

    # @handler("on_menu_select")
    # def handle_menu_select(self, id):
    #     self.change_view(views.PendantDropConfiguration) # change view by name.









