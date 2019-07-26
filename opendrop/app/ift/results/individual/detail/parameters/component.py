import math

from gi.repository import Gtk

from opendrop.mvp import ComponentSymbol, View, Presenter
from opendrop.utility.bindable import Bindable, AccessorBindable

parameters_cs = ComponentSymbol()  # type: ComponentSymbol[Gtk.Widget]


@parameters_cs.view()
class ParametersView(View['ParametersPresenter', Gtk.Widget]):
    def _do_init(self) -> Gtk.Widget:
        self._widget = Gtk.Grid(row_spacing=10, hexpand=False, width_request=220)

        parameters_lbl = Gtk.Label(xalign=0)
        parameters_lbl.set_markup('<b>Parameters</b>')
        self._widget.attach(parameters_lbl, 0, 0, 1, 1)

        sheet = Gtk.Grid(row_spacing=10, column_spacing=10)
        self._widget.attach(sheet, 0, 1, 1, 1)

        interfacial_tension_lbl = Gtk.Label('IFT (mN/m):', xalign=0)
        sheet.attach(interfacial_tension_lbl, 0, 0, 1, 1)

        volume_lbl = Gtk.Label('Volume (mm²):', xalign=0)
        sheet.attach(volume_lbl, 0, 1, 1, 1)

        surface_area_lbl = Gtk.Label('Surface area (mm³):', xalign=0)
        sheet.attach(surface_area_lbl, 0, 2, 1, 1)

        sheet.attach(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL, hexpand=True), 0, 3, 2, 1)

        worthington_lbl = Gtk.Label('Worthington:', xalign=0)
        sheet.attach(worthington_lbl, 0, 4, 1, 1)

        bond_number_lbl = Gtk.Label('Bond number:', xalign=0)
        sheet.attach(bond_number_lbl, 0, 5, 1, 1)

        apex_coords_lbl = Gtk.Label('Apex coordinates (px):', xalign=0)
        sheet.attach(apex_coords_lbl, 0, 6, 1, 1)

        image_angle_lbl = Gtk.Label('Image angle:', xalign=0)
        sheet.attach(image_angle_lbl, 0, 7, 1, 1)

        interfacial_tension_val = Gtk.Label(xalign=0)
        sheet.attach_next_to(interfacial_tension_val, interfacial_tension_lbl, Gtk.PositionType.RIGHT, 1, 1)

        volume_val = Gtk.Label(xalign=0)
        sheet.attach_next_to(volume_val, volume_lbl, Gtk.PositionType.RIGHT, 1, 1)

        surface_area_val = Gtk.Label(xalign=0)
        sheet.attach_next_to(surface_area_val, surface_area_lbl, Gtk.PositionType.RIGHT, 1, 1)

        worthington_val = Gtk.Label(xalign=0)
        sheet.attach_next_to(worthington_val, worthington_lbl, Gtk.PositionType.RIGHT, 1, 1)

        bond_number_val = Gtk.Label(xalign=0)
        sheet.attach_next_to(bond_number_val, bond_number_lbl, Gtk.PositionType.RIGHT, 1, 1)

        apex_coords_val = Gtk.Label(xalign=0)
        sheet.attach_next_to(apex_coords_val, apex_coords_lbl, Gtk.PositionType.RIGHT, 1, 1)

        image_angle_val = Gtk.Label(xalign=0)
        sheet.attach_next_to(image_angle_val, image_angle_lbl, Gtk.PositionType.RIGHT, 1, 1)

        self._widget.foreach(Gtk.Widget.show_all)

        self.bn_interfacial_tension = AccessorBindable(
            setter=(
                lambda v:
                    interfacial_tension_val.set_text('{:.4g}'.format(v * 1e3))
            )
        )

        self.bn_volume = AccessorBindable(
            setter=(
                lambda v:
                    volume_val.set_text('{:.4g}'.format(v * 1e9))
            )
        )

        self.bn_surface_area = AccessorBindable(
            setter=(
                lambda v:
                    surface_area_val.set_text('{:.4g}'.format(v * 1e6))
            )
        )

        self.bn_worthington = AccessorBindable(
            setter=(
                lambda v:
                    worthington_val.set_text('{:.4g}'.format(v))
            )
        )

        self.bn_bond_number = AccessorBindable(
            setter=(
                lambda v:
                    bond_number_val.set_text('{:.4g}'.format(v))
            )
        )

        self.bn_apex_coords = AccessorBindable(
            setter=(
                lambda v:
                    apex_coords_val.set_text('({0[0]:.4g}, {0[1]:.4g})'.format(v))
            )
        )

        self.bn_image_angle = AccessorBindable(
            setter=(
                lambda v:
                    image_angle_val.set_text('{:.4g}°'.format(math.degrees(v)))
            )
        )

        self.presenter.view_ready()

        return self._widget

    def _do_destroy(self) -> None:
        self._widget.destroy()


@parameters_cs.presenter(
    options=[
        'in_interfacial_tension',
        'in_volume',
        'in_surface_area',
        'in_worthington',
        'in_bond_number',
        'in_apex_coords',
        'in_image_angle',
    ]
)
class ParametersPresenter(Presenter['ParametersView']):
    def _do_init(
            self,
            in_interfacial_tension: Bindable[float],
            in_volume: Bindable[float],
            in_surface_area: Bindable[float],
            in_worthington: Bindable[float],
            in_bond_number: Bindable[float],
            in_apex_coords: Bindable[float],
            in_image_angle: Bindable[float],
    ) -> None:
        self._bn_interfacial_tension = in_interfacial_tension
        self._bn_volume = in_volume
        self._bn_surface_area = in_surface_area
        self._bn_worthington = in_worthington
        self._bn_bond_number = in_bond_number
        self._bn_apex_coords = in_apex_coords
        self._bn_image_angle = in_image_angle

        self.__data_bindings = []

    def view_ready(self):
        self.__data_bindings.extend([
            self._bn_interfacial_tension.bind(self.view.bn_interfacial_tension),
            self._bn_volume.bind(self.view.bn_volume),
            self._bn_surface_area.bind(self.view.bn_surface_area),
            self._bn_worthington.bind(self.view.bn_worthington),
            self._bn_bond_number.bind(self.view.bn_bond_number),
            self._bn_apex_coords.bind(self.view.bn_apex_coords),
            self._bn_image_angle.bind(self.view.bn_image_angle),
        ])

    def _do_destroy(self) -> None:
        for db in self.__data_bindings:
            db.unbind()
