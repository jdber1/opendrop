from typing import Optional, Any

from gi.repository import Gtk

from opendrop.app.common.image_acquirer import ImageAcquirer, LocalStorageAcquirer, USBCameraAcquirer
from opendrop.mvp import ComponentSymbol, View, Presenter
from opendrop.utility.bindable import Bindable
from .local_storage import local_storage_cs
from .usb_camera import usb_camera_cs

configurator_cs = ComponentSymbol()  # type: ComponentSymbol[Gtk.Widget]


@configurator_cs.view()
class ConfiguratorView(View['ConfiguratorPresenter', Gtk.Widget]):
    def _do_init(self) -> Gtk.Widget:
        self._widget = Gtk.Grid()

        self._configurator_cid = None  # type: Optional[Any]

        self.presenter.view_ready()

        return self._widget

    def load_local_storage_configurator(self) -> None:
        self.remove_configurator()
        acquirer = self.presenter.bn_acquirer.get()

        self._configurator_cid, configurator_area = self.new_component(
            local_storage_cs.factory(
                acquirer=acquirer
            )
        )
        configurator_area.show()
        self._widget.add(configurator_area)

    def load_usb_camera_configurator(self) -> None:
        self.remove_configurator()
        acquirer = self.presenter.bn_acquirer.get()

        self._configurator_cid, configurator_area = self.new_component(
            usb_camera_cs.factory(
                acquirer=acquirer
            )
        )
        configurator_area.show()
        self._widget.add(configurator_area)

    def remove_configurator(self) -> None:
        if self._configurator_cid is None:
            return

        self.remove_component(self._configurator_cid)

    def _do_destroy(self) -> None:
        self._widget.destroy()


@configurator_cs.presenter(options=['in_acquirer'])
class ConfiguratorPresenter(Presenter['ConfiguratorView']):
    def _do_init(self, in_acquirer: Bindable[ImageAcquirer]) -> None:
        self.bn_acquirer = in_acquirer
        self.__event_connections = []

    def view_ready(self) -> None:
        self.__event_connections.extend([
            self.bn_acquirer.on_changed.connect(
                self._hdl_acquirer_changed
            )
        ])

        self._hdl_acquirer_changed()

    def _hdl_acquirer_changed(self) -> None:
        acquirer = self.bn_acquirer.get()
        if acquirer is None:
            self.view.remove_configurator()
            return

        if isinstance(acquirer, LocalStorageAcquirer):
            self.view.load_local_storage_configurator()
        elif isinstance(acquirer, USBCameraAcquirer):
            self.view.load_usb_camera_configurator()
        else:
            raise ValueError(
                "No configurator available for acquirer '{}'"
                .format(acquirer)
            )

    def _do_destroy(self) -> None:
        for ec in self.__event_connections:
            ec.disconnect()
