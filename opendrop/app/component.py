from opendrop.mvp import ComponentSymbol, View, Presenter
from .conan import ConanSession, conan_root_cs
from .ift import IFTSession, ift_root_cs
from .main_menu import main_menu_cs
from .model import AppRootModel, AppMode

app_cs = ComponentSymbol()  # type: ComponentSymbol[None]


@app_cs.view()
class AppRootView(View['AppRootPresenter', None]):
    def _do_init(self) -> None:
        _, self._main_menu_window = self.new_component(
            main_menu_cs.factory(
                model=self.presenter.main_menu_model
            )
        )

        self._ift_window_cid = None
        self._conan_window_cid = None

        self.presenter.view_ready()

    def start_ift(self, session: IFTSession) -> None:
        assert self._ift_window_cid is None

        self._ift_window_cid, ift_window = self.new_component(
            ift_root_cs.factory(
                session=session
            )
        )

        self._main_menu_window.hide()
        ift_window.show()

    def _end_ift(self) -> None:
        assert self._ift_window_cid is not None
        self.remove_component(self._ift_window_cid)
        self._ift_window_cid = None

    def start_conan(self, session: ConanSession) -> None:
        assert self._conan_window_cid is None

        self._conan_window_cid, conan_window = self.new_component(
            conan_root_cs.factory(
                session=session
            )
        )

        self._main_menu_window.hide()
        conan_window.show()

    def _end_conan(self) -> None:
        assert self._conan_window_cid is not None
        self.remove_component(self._conan_window_cid)
        self._conan_window_cid = None

    def return_to_main_menu(self) -> None:
        if self._ift_window_cid is not None:
            self._end_ift()

        if self._conan_window_cid is not None:
            self._end_conan()

        self._main_menu_window.show()

    def hide_all_windows(self) -> None:
        self._main_menu_window.hide()
        self._ift_window.hide()


@app_cs.presenter(options=['model'])
class AppRootPresenter(Presenter['AppRootView']):
    def _do_init(self, model: AppRootModel) -> None:
        self._model = model

        self.main_menu_model = model.main_menu

        self.__event_connections = []

    def view_ready(self) -> None:
        self.__event_connections.extend([
            self._model.bn_mode.on_changed.connect(
                self._hdl_model_mode_changed
            )
        ])

        self._hdl_model_mode_changed()

    def _hdl_model_mode_changed(self) -> None:
        mode = self._model.bn_mode.get()

        if mode is AppMode.MAIN_MENU:
            self.view.return_to_main_menu()
        elif mode is AppMode.IFT:
            new_ift_session = self._model.new_ift_session()
            self.view.start_ift(new_ift_session)
        elif mode is AppMode.CONAN:
            new_conan_session = self._model.new_conan_session()
            self.view.start_conan(new_conan_session)
        elif mode is AppMode.QUIT:
            self.component_destroy()

    def _do_destroy(self) -> None:
        for ec in self.__event_connections:
            ec.disconnect()
