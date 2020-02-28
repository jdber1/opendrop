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


import math
from typing import Tuple

from gi.repository import Gtk

from opendrop.mvp import ComponentSymbol, View, Presenter
from opendrop.utility.bindable.gextension import GObjectPropertyBindable
from opendrop.utility.bindable.typing import ReadBindable, WriteBindable

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

        volume_lbl = Gtk.Label('Volume (mm³):', xalign=0)
        sheet.attach(volume_lbl, 0, 1, 1, 1)

        surface_area_lbl = Gtk.Label('Surface area (mm²):', xalign=0)
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

        self.bn_interfacial_tension = GObjectPropertyBindable(
            interfacial_tension_val,
            'label',
            transform_to=lambda v: '{:.4g}'.format(v * 1e3),
        )  # type: WriteBindable[float]

        self.bn_volume = GObjectPropertyBindable(
            volume_val,
            'label',
            transform_to=lambda v: '{:.4g}'.format(v * 1e9),
        )  # type: WriteBindable[float]

        self.bn_surface_area = GObjectPropertyBindable(
            surface_area_val,
            'label',
            transform_to=lambda v: '{:.4g}'.format(v * 1e6),
        )  # type: WriteBindable[float]

        self.bn_worthington = GObjectPropertyBindable(
            worthington_val,
            'label',
            transform_to=lambda v: '{:.4g}'.format(v),
        )  # type: WriteBindable[float]

        self.bn_bond_number = GObjectPropertyBindable(
            bond_number_val,
            'label',
            transform_to=lambda v: '{:.4g}'.format(v),
        )  # type: WriteBindable[float]

        self.bn_apex_coords = GObjectPropertyBindable(
            apex_coords_val,
            'label',
            transform_to=lambda v: '({0[0]:.4g}, {0[1]:.4g})'.format(v)
        )  # type: WriteBindable[Tuple[float, float]]

        self.bn_image_angle = GObjectPropertyBindable(
            image_angle_val,
            'label',
            transform_to=lambda v: '{:.4g}°'.format(math.degrees(v))
        )  # type: WriteBindable[float]

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
            in_interfacial_tension: ReadBindable[float],
            in_volume: ReadBindable[float],
            in_surface_area: ReadBindable[float],
            in_worthington: ReadBindable[float],
            in_bond_number: ReadBindable[float],
            in_apex_coords: ReadBindable[Tuple[float, float]],
            in_image_angle: ReadBindable[float],
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
            self._bn_interfacial_tension.bind_to(self.view.bn_interfacial_tension),
            self._bn_volume.bind_to(self.view.bn_volume),
            self._bn_surface_area.bind_to(self.view.bn_surface_area),
            self._bn_worthington.bind_to(self.view.bn_worthington),
            self._bn_bond_number.bind_to(self.view.bn_bond_number),
            self._bn_apex_coords.bind_to(self.view.bn_apex_coords),
            self._bn_image_angle.bind_to(self.view.bn_image_angle),
        ])

    def _do_destroy(self) -> None:
        for db in self.__data_bindings:
            db.unbind()
