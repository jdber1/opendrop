from gi.repository import Gtk

from opendrop.app.common.footer.linearnav import linear_navigator_footer_cs
from opendrop.app.common.wizard import WizardPageControls
from opendrop.mvp import ComponentSymbol, View, Presenter
from opendrop.utility.bindablegext import GObjectPropertyBindable
from opendrop.widgets.float_entry import FloatEntry
from .model import PhysicalParametersModel

physical_parameters_cs = ComponentSymbol()  # type: ComponentSymbol[Gtk.Widget]


@physical_parameters_cs.view(options=['footer_area'])
class PhysicalParametersView(View['PhysicalParametersPresenter', Gtk.Widget]):
    def _do_init(self, footer_area: Gtk.Grid) -> Gtk.Widget:
        self._widget = Gtk.Grid(margin=20, row_spacing=10, column_spacing=10)

        # Label widgets
        inner_density_lbl = Gtk.Label('Inner density (kg/m³):', xalign=0)
        self._widget.attach(inner_density_lbl, 0, 0, 1, 1)

        outer_density_lbl = Gtk.Label('Outer density (kg/m³):', xalign=0)
        self._widget.attach(outer_density_lbl, 0, 1, 1, 1)

        needle_width_lbl = Gtk.Label('Needle diameter (mm):', xalign=0)
        self._widget.attach(needle_width_lbl, 0, 2, 1, 1)

        gravity_lbl = Gtk.Label('Gravity (m/s²):', xalign=0)
        self._widget.attach(gravity_lbl, 0, 3, 1, 1)

        # Input widgets
        self._inner_density_inp = FloatEntry(lower=0, width_chars=10)
        self._widget.attach_next_to(self._inner_density_inp, inner_density_lbl, Gtk.PositionType.RIGHT, 1, 1)

        self._outer_density_inp = FloatEntry(lower=0, width_chars=10)
        self._widget.attach_next_to(self._outer_density_inp, outer_density_lbl, Gtk.PositionType.RIGHT, 1, 1)

        self._needle_width_inp = FloatEntry(lower=0, width_chars=10)
        self._widget.attach_next_to(self._needle_width_inp, needle_width_lbl, Gtk.PositionType.RIGHT, 1, 1)

        self._gravity_inp = FloatEntry(lower=0, width_chars=10)
        self._widget.attach_next_to(self._gravity_inp, gravity_lbl, Gtk.PositionType.RIGHT, 1, 1)

        self._inner_density_err_msg_lbl = Gtk.Label(xalign=0)
        self._inner_density_err_msg_lbl.get_style_context().add_class('error-text')
        self._widget.attach_next_to(self._inner_density_err_msg_lbl, self._inner_density_inp, Gtk.PositionType.RIGHT, 1, 1)

        self._outer_density_err_msg_lbl = Gtk.Label(xalign=0)
        self._outer_density_err_msg_lbl.get_style_context().add_class('error-text')
        self._widget.attach_next_to(self._outer_density_err_msg_lbl, self._outer_density_inp, Gtk.PositionType.RIGHT, 1, 1)

        self._needle_width_err_msg_lbl = Gtk.Label(xalign=0)
        self._needle_width_err_msg_lbl.get_style_context().add_class('error-text')
        self._widget.attach_next_to(self._needle_width_err_msg_lbl, self._needle_width_inp, Gtk.PositionType.RIGHT, 1, 1)

        self._gravity_err_msg_lbl = Gtk.Label(xalign=0)
        self._gravity_err_msg_lbl.get_style_context().add_class('error-text')
        self._widget.attach_next_to(self._gravity_err_msg_lbl, self._gravity_inp, Gtk.PositionType.RIGHT, 1, 1)

        self._widget.show_all()

        self.bn_inner_density = GObjectPropertyBindable(
            g_obj=self._inner_density_inp,
            prop_name='value',
        )

        self.bn_outer_density = GObjectPropertyBindable(
            g_obj=self._outer_density_inp,
            prop_name='value',
        )

        self.bn_needle_width = GObjectPropertyBindable(
            g_obj=self._needle_width_inp,
            prop_name='value',
            # Needle width shown to user is in millimetres.
            transform_from=lambda x: x / 1000 if x is not None else None,
            transform_to=lambda x: x * 1000 if x is not None else None,
        )

        self.bn_gravity = GObjectPropertyBindable(
            g_obj=self._gravity_inp,
            prop_name='value',
        )

        _, footer_inside = self.new_component(
            linear_navigator_footer_cs.factory(
                do_back=self.presenter.prev_page,
                do_next=self.presenter.next_page,
            )
        )
        footer_inside.show()
        footer_area.add(footer_inside)

        self.presenter.view_ready()

        return self._widget

    def _do_destroy(self) -> None:
        self._widget.destroy()


@physical_parameters_cs.presenter(options=['model', 'page_controls'])
class PhysicalParametersPresenter(Presenter['PhysicalParametersView']):
    def _do_init(self, model: PhysicalParametersModel, page_controls: WizardPageControls) -> None:
        self._model = model
        self._page_controls = page_controls

        self.__data_bindings = []

    def view_ready(self) -> None:
        self.__data_bindings.extend([
            self._model.bn_inner_density.bind(
                self.view.bn_inner_density
            ),
            self._model.bn_outer_density.bind(
                self.view.bn_outer_density
            ),
            self._model.bn_needle_width.bind(
                self.view.bn_needle_width
            ),
            self._model.bn_gravity.bind(
                self.view.bn_gravity
            ),
        ])

    def prev_page(self) -> None:
        self._page_controls.prev_page()

    def next_page(self) -> None:
        self._page_controls.next_page()

    def _do_destroy(self) -> None:
        for db in self.__data_bindings:
            db.unbind()
