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


import itertools

from gi.repository import Gtk, GObject

from opendrop.utility.bindable.gextension import GObjectPropertyBindable
from opendrop.utility.bindable.binding import Binding
from opendrop.mvp import ComponentSymbol, View, Presenter
from opendrop.widgets.float_entry import FloatEntry
from opendrop.app.common.image_processing.image_processor import ImageProcessorPluginViewContext
from opendrop.app.conan.image_processing.services.plugins import ToolID

from .model import ConanThreshPluginModel

conan_thresh_plugin_cs = ComponentSymbol()  # type: ComponentSymbol[None]


@conan_thresh_plugin_cs.view(options=['view_context'])
class ConanThreshPluginView(View['ConanThreshPluginPresenter', None]):
    _STYLE = '''
        .small-pad {
             min-height: 0px;
             min-width: 0px;
             padding: 6px 4px 6px 4px;
        }
    '''

    _STYLE_PROV = Gtk.CssProvider()
    _STYLE_PROV.load_from_data(bytes(_STYLE, 'utf-8'))

    def _do_init(self, view_context: ImageProcessorPluginViewContext) -> None:
        self._view_context = view_context
        self._tool_ref = self._view_context.get_tool_item(ToolID.THRESH)

        self.bn_tool_button_is_active = self._tool_ref.bn_is_active

        self._button_body = Gtk.Grid(hexpand=True, vexpand=True)
        self._tool_ref.button_interior.add(self._button_body)

        button_lbl = Gtk.Label(
            label="Edge Threshold",
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
            row_spacing=10,
            column_spacing=10,
            width_request=250,
        )
        self._popover.add(popover_body)

        thresh_inp = Gtk.Adjustment(value=0, lower=0, upper=100)

        thresh_lbl = Gtk.Label('% of max:', halign=Gtk.Align.START)
        popover_body.attach(thresh_lbl, 0, 0, 1, 1)

        thresh_scl = Gtk.Scale(
            orientation=Gtk.Orientation.HORIZONTAL,
            adjustment=thresh_inp,
            hexpand=True,
            draw_value=False
        )
        thresh_scl.get_style_context().add_class('small-pad')
        thresh_scl.get_style_context().add_provider(self._STYLE_PROV, Gtk.STYLE_PROVIDER_PRIORITY_USER)
        thresh_scl.show()
        popover_body.attach(thresh_scl, 1, 0, 1, 1)

        thresh_ety = FloatEntry(
            width_chars=5,
            xalign=0
        )
        thresh_ety.get_style_context().add_class('small-pad')
        thresh_ety.get_style_context().add_provider(self._STYLE_PROV, Gtk.STYLE_PROVIDER_PRIORITY_USER)
        thresh_ety.show()
        popover_body.attach(thresh_ety, 2, 0, 1, 1)

        # Bind the properties of Gtk.Adjustment to the Gtk.Entry widget.
        for (src, targ), prop in itertools.product(
                ((thresh_inp, thresh_ety),),
                ('value', 'lower', 'upper')
        ):
            src.bind_property(
                prop,                               # source_property
                targ, prop,                         # target, target_property
                GObject.BindingFlags.BIDIRECTIONAL  # flags
                | GObject.BindingFlags.SYNC_CREATE,
                lambda _, v: round(v, 1),           # transform_to
                lambda _, v: v                      # transform_from
            )

        self.bn_thresh = GObjectPropertyBindable(
            g_obj=thresh_inp,
            prop_name='value',
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


@conan_thresh_plugin_cs.presenter(options=['model'])
class ConanThreshPluginPresenter(Presenter['ConanThreshPluginView']):
    def _do_init(self, model: ConanThreshPluginModel) -> None:
        self._model = model
        self.__data_bindings = []
        self.__event_connections = []

    def view_ready(self) -> None:
        self.__data_bindings.extend([
            Binding(src=self._model.bn_thresh,
                    dst=self.view.bn_thresh,
                    to_dst=lambda x: x*100,
                    to_src=lambda x: x/100),
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
