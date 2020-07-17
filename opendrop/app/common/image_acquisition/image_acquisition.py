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


from gi.repository import Gtk
from injector import inject

from opendrop.app.common.services.acquisition import AcquirerType, ImageAcquisitionService
from opendrop.appfw import Presenter, TemplateChild, component

from .configurator import configurator_cs


@component(
    template_path='./image_acquisition.ui',
)
class ImageAcquisitionPresenter(Presenter):
    combo_box = TemplateChild('combo_box')  # type: TemplateChild[Gtk.ComboBoxText]
    configure_area = TemplateChild('configure_area')  # type: TemplateChild[Gtk.Container]

    @inject
    def __init__(self, acquisition_service: ImageAcquisitionService) -> None:
        self.acquisition_service = acquisition_service
        self.event_connections = ()

    def after_view_init(self) -> None:
        self.populate_combobox()

        self.configurator_component = configurator_cs.factory(
            in_acquirer=self.acquisition_service.bn_acquirer
        ).create()
        self.configurator_component.view_rep.show()
        self.configure_area.add(self.configurator_component.view_rep)

        self.event_connections = (
            self.acquisition_service.bn_acquirer.on_changed.connect(self.acquisition_service_acquirer_changed),
        )

        self.combo_box.connect('notify::active-id', self.combo_box_active_id_changed)

        self.acquisition_service_acquirer_changed()

    def combo_box_active_id_changed(self, *_) -> None:
        active_id = self.combo_box.props.active_id
        if active_id is not None:
            self.acquisition_service.use_acquirer_type(AcquirerType[active_id])
        else:
            self.acquisition_service.use_acquirer_type(None)

    def acquisition_service_acquirer_changed(self, *_) -> None:
        acquirer_type = self.acquisition_service.get_acquirer_type()
        if acquirer_type is not None:
            self.combo_box.props.active_id = acquirer_type.name
        else:
            self.combo_box.props.active_id = None

    def populate_combobox(self) -> None:
        for typ in AcquirerType:
            self.combo_box.append(id=typ.name, text=typ.display_name)

    def destroy(self, *_) -> None:
        for conn in self.event_connections:
            conn.disconnect()

        self.configurator_component.destroy()
