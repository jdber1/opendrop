import itertools

from gi.repository import Gtk, GObject

from opendrop.app.common.image_processing.image_processor import ImageProcessorPluginViewContext
from opendrop.app.conan.image_processing.plugins import ToolID
from opendrop.mvp import ComponentSymbol, View, Presenter
from opendrop.utility.bindablegext import GObjectPropertyBindable
from opendrop.widgets.float_entry import FloatEntry
from .model import ForegroundDetectionPluginModel

foreground_detection_plugin_cs = ComponentSymbol()  # type: ComponentSymbol[None]


@foreground_detection_plugin_cs.view(options=['view_context'])
class ForegroundDetectionPluginView(View['ForegroundDetectionPluginPresenter', None]):
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
        self._tool_ref = self._view_context.get_tool_item(ToolID.FOREGROUND_DETECTION)

        self.bn_tool_button_is_active = self._tool_ref.bn_is_active

        self._button_body = Gtk.Grid(hexpand=True, vexpand=True)
        self._tool_ref.button_interior.add(self._button_body)

        button_lbl = Gtk.Label(
            label="Foreground detection",
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

        thresh_inp = Gtk.Adjustment(value=255, lower=1, upper=255)

        thresh_lbl = Gtk.Label('Threshold:', halign=Gtk.Align.START)
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


@foreground_detection_plugin_cs.presenter(options=['model'])
class ForegroundDetectionPluginPresenter(Presenter['ForegroundDetectionPluginView']):
    def _do_init(self, model: ForegroundDetectionPluginModel) -> None:
        self._model = model
        self.__data_bindings = []
        self.__event_connections = []

    def view_ready(self) -> None:
        self.__data_bindings.extend([
            self._model.bn_thresh.bind(
                self.view.bn_thresh
            ),
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
