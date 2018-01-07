from abc import abstractmethod

from opendrop.mvp.IView import IView


class IMainView(IView):
    @abstractmethod
    def show_about_dialog(self): pass