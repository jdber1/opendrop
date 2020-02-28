# Copyright © 2020, Joseph Berry, Rico Tabor (opendrop.dev@gmail.com)
# OpenDrop is released under the GNU GPL License. You are free to
# modify and distribute the code, but always under the same license
# (i.e. you cannot make commercial derivatives).
#
# If you use this software in your research, please cite the following
# journal articles:
#
# J. D. Berry, M. J. Neeson, R. R. Dagastine, D. Y. C. Chan and
# R. F. Tabor, Measurement of surface and interfacial tension using
# pendant drop tensiometry. Journal of Colloid and Interface Science 454
# (2015) 226–237. https://doi.org/10.1016/j.jcis.2015.05.012
#
#E. Huang, T. Denning, A. Skoufis, J. Qi, R. R. Dagastine, R. F. Tabor
#and J. D. Berry, OpenDrop: Open-source software for pendant drop
#tensiometry & contact angle measurements, submitted to the Journal of
# Open Source Software
#
#These citations help us not only to understand who is using and
#developing OpenDrop, and for what purpose, but also to justify
#continued development of this code and other open source resources.
#
# OpenDrop is distributed WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this software.  If not, see <https://www.gnu.org/licenses/>.
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
