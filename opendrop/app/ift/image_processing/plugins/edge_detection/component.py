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
from gi.repository import Gtk

from opendrop.app.common.image_processing.image_processor import ImageProcessorPluginViewContext
from opendrop.app.ift.image_processing.plugins import ToolID
from opendrop.mvp import ComponentSymbol, View, Presenter
from opendrop.utility.bindablegext import GObjectPropertyBindable
from opendrop.widgets.canny_parameters import CannyParameters
from .model import EdgeDetectionPluginModel

edge_detection_plugin_cs = ComponentSymbol()  # type: ComponentSymbol[None]


@edge_detection_plugin_cs.view(options=['view_context'])
class EdgeDetectionPluginView(View['EdgeDetectionPluginPresenter', None]):
    def _do_init(self, view_context: ImageProcessorPluginViewContext) -> None:
        self._view_context = view_context
        self._tool_ref = self._view_context.get_tool_item(ToolID.EDGE_DETECTION)

        self.bn_tool_button_is_active = self._tool_ref.bn_is_active

        self._button_body = Gtk.Grid(hexpand=True, vexpand=True)
        self._tool_ref.button_interior.add(self._button_body)

        button_lbl = Gtk.Label(
            label="Edge detection",
            vexpand=True,
            valign=Gtk.Align.CENTER,
        )
        self._button_body.add(button_lbl)

        self._button_body.show_all()

        self._popover = Gtk.Popover(
            relative_to=self._button_body,
            modal=False,
        )

        # Prevent the popover from being dismissed by the user clicking on it.
        self._popover.connect('button-release-event', lambda *_: True)

        popover_body = Gtk.Grid(
            margin=10,
            width_request=250,
        )
        self._popover.add(popover_body)

        canny_adjuster = CannyParameters()
        popover_body.add(canny_adjuster)

        self.bn_canny_min = GObjectPropertyBindable(
            g_obj=canny_adjuster,
            prop_name='min-thresh',
        )

        self.bn_canny_max = GObjectPropertyBindable(
            g_obj=canny_adjuster,
            prop_name='max-thresh',
        )

        popover_body.show_all()

        self.presenter.view_ready()

    def show_popover(self) -> None:
        self._popover.popup()

    def hide_popover(self) -> None:
        self._popover.popdown()

    def _do_destroy(self) -> None:
        self._button_body.destroy()
        self._popover.destroy()


@edge_detection_plugin_cs.presenter(options=['model'])
class EdgeDetectionPluginPresenter(Presenter['EdgeDetectionPluginView']):
    def _do_init(self, model: EdgeDetectionPluginModel) -> None:
        self._model = model
        self.__data_bindings = []
        self.__event_connections = []

    def view_ready(self) -> None:
        self.__data_bindings.extend([
            self._model.bn_canny_min.bind(
                self.view.bn_canny_min
            ),
            self._model.bn_canny_max.bind(
                self.view.bn_canny_max
            )
        ])

        self.__event_connections.extend([
            self.view.bn_tool_button_is_active.on_changed.connect(
                self._hdl_tool_button_is_active_changed
            )
        ])

        self._hdl_tool_button_is_active_changed()

    def _hdl_tool_button_is_active_changed(self) -> None:
        is_active = self.view.bn_tool_button_is_active.get()
        if is_active:
            self.view.show_popover()
        else:
            self.view.hide_popover()

    def _do_destroy(self) -> None:
        for db in self.__data_bindings:
            db.unbind()

        for ec in self.__event_connections:
            ec.disconnect()
