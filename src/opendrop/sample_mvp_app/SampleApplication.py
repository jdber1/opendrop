from opendrop.sample_mvp_app.bases.GtkApplication import GtkApplication

from opendrop.sample_mvp_app.SampleAppModel import SampleAppModel

from opendrop.sample_mvp_app.presenters.BurgerExamplePresenter import BurgerExamplePresenter
from opendrop.sample_mvp_app.presenters.MainPresenter import MainPresenter
from opendrop.sample_mvp_app.presenters.TimerExamplePresenter import TimerExamplePresenter

from opendrop.sample_mvp_app.views.BurgerExampleView import BurgerExampleView
from opendrop.sample_mvp_app.views.MainView import MainView
from opendrop.sample_mvp_app.views.TimerExampleView import TimerExampleView


class SampleApplication(GtkApplication):
    APPLICATION_ID = 'org.example.sampleapp'

    MODEL = SampleAppModel
    VIEWS = [MainView, TimerExampleView, BurgerExampleView]
    PRESENTERS = [MainPresenter, TimerExamplePresenter, BurgerExamplePresenter]

    ENTRY_VIEW = MainView
