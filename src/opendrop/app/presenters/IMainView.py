from abc import abstractmethod

from opendrop.app.bases.IMaximizable import IMaximizable
from opendrop.mvp.IView import IView


class IMainView(IView, IMaximizable):
    @abstractmethod
    def show_about_dialog(self): pass