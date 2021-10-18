# Copyright © 2020, Joseph Berry, Rico Tabor (opendrop.dev@gmail.com)
# OpenDrop is released under the GNU GPL License. You are free to
# modify and distribute the code, but always under the same license
#
# If you use this software in your research, please cite the following
# journal articles:
#
# J. D. Berry, M. J. Neeson, R. R. Dagastine, D. Y. C. Chan and
# R. F. Tabor, Measurement of surface and interfacial tension using
# pendant drop tensiometry. Journal of Colloid and Interface Science 454
# (2015) 226–237. https://doi.org/10.1016/j.jcis.2015.05.012
#
# E. Huang, T. Denning, A. Skoufis, J. Qi, R. R. Dagastine, R. F. Tabor
# and J. D. Berry, OpenDrop: Open-source software for pendant drop
# tensiometry & contact angle measurements, submitted to the Journal of
# Open Source Software
#
# These citations help us not only to understand who is using and
# developing OpenDrop, and for what purpose, but also to justify
# continued development of this code and other open source resources.
#
# OpenDrop is distributed WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this software.  If not, see <https://www.gnu.org/licenses/>.


from typing import Any, Optional

from gi.repository import GObject, Gtk
from injector import inject

from opendrop.app.common.services.acquisition import (
    GenicamAcquirer,
    ImageAcquirer,
    LocalStorageAcquirer,
    USBCameraAcquirer,
)
from opendrop.appfw import ComponentFactory, Presenter, component, install

from .local_storage import local_storage_cs


@component(
    template_path='./configurator.ui',
)
class ImageAcquisitionConfiguratorPresenter(Presenter[Gtk.Bin]):
    view_ready = False

    _acquirer = None  # type: Optional[ImageAcquirer]

    @inject
    def __init__(self, cf: ComponentFactory) -> None:
        self.cf = cf
        self.configurator_component = None  # type: Optional[Any]

    def after_view_init(self) -> None:
        self.view_ready = True
        self.update_configurator()

    def update_configurator(self):
        if not self.view_ready: return

        acquirer = self._acquirer
        if acquirer is None:
            self.remove_configurator()
        elif isinstance(acquirer, LocalStorageAcquirer):
            self.load_local_storage_configurator()
        elif isinstance(acquirer, USBCameraAcquirer):
            self.load_usb_camera_configurator()
        elif isinstance(acquirer, GenicamAcquirer):
            self.load_genicam_configurator()
        else:
            raise ValueError(
                "No configurator available for acquirer '{}'"
                .format(acquirer)
            )

    @install
    @GObject.Property
    def acquirer(self) -> Optional[ImageAcquirer]:
        return self._acquirer

    @acquirer.setter
    def acquirer(self, acquirer: Optional[ImageAcquirer]):
        self._acquirer = acquirer
        self.update_configurator()

    def load_local_storage_configurator(self) -> None:
        self.remove_configurator()

        self.configurator_component = local_storage_cs.factory(
            acquirer=self._acquirer
        ).create()

        self.configurator_component.view_rep.show()
        self.host.add(self.configurator_component.view_rep)

    def load_usb_camera_configurator(self) -> None:
        self.remove_configurator()

        configurator = self.cf.create(
            'ImageAcquisitionConfiguratorUSBCamera',
            acquirer=self._acquirer,
            visible=True,
        )

        self.host.add(configurator)

    def load_genicam_configurator(self) -> None:
        self.remove_configurator()

        configurator = self.cf.create(
            'ImageAcquisitionConfiguratorGenicam',
            acquirer=self._acquirer,
            visible=True,
        )

        self.host.add(configurator)

    def remove_configurator(self) -> None:
        if self.configurator_component is not None:
            self.configurator_component.destroy()
            self.configurator_component = None

        child = self.host.get_child()
        if child is not None:
            child.destroy()

    def destroy(self, *_) -> None:
        self.remove_configurator()
