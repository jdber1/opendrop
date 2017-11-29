from abc import abstractmethod

from opendrop.mvp.IView import IView

from opendrop.sample_app.bases.IMaximizable import IMaximizable


class IMainView(IView, IMaximizable):
    @abstractmethod
    def show_about_dialog(self): pass