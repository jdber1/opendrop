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


from typing import Optional
from gi.repository import Gtk, GObject

from opendrop.appfw import componentclass, Inject

# The FloatEntry widget is referenced in the component template, import it now to make sure it's registered
# with the GLib type system.
from opendrop.widgets.float_entry import FloatEntry

from .services.physical_parameters import PhysicalParametersFormModel


@componentclass(
    template_path='./physical_parameters.ui',
)
class IFTPhysicalParametersForm(Gtk.Grid):
    __gtype_name__ = 'IFTPhysicalParametersForm'

    _form = Inject(PhysicalParametersFormModel)

    def __init__(self, **properties) -> None:
        super().__init__(**properties)

        self._form.bn_inner_density.on_changed.connect(lambda: self.notify('inner-density'), weak_ref=False)
        self._form.bn_outer_density.on_changed.connect(lambda: self.notify('outer-density'), weak_ref=False)
        self._form.bn_needle_width.on_changed.connect(lambda: self.notify('needle-width'), weak_ref=False)
        self._form.bn_gravity.on_changed.connect(lambda: self.notify('gravity'), weak_ref=False)

    @GObject.Property
    def inner_density(self) -> Optional[float]:
        return self._form.bn_inner_density.get()

    @inner_density.setter
    def inner_density(self, value: Optional[float]) -> None:
        self._form.bn_inner_density.set(value)

    @GObject.Property
    def outer_density(self) -> Optional[float]:
        return self._form.bn_outer_density.get()

    @outer_density.setter
    def outer_density(self, value: Optional[float]) -> None:
        self._form.bn_outer_density.set(value)

    @GObject.Property
    def gravity(self) -> Optional[float]:
        return self._form.bn_gravity.get()

    @gravity.setter
    def gravity(self, value: Optional[float]) -> None:
        self._form.bn_gravity.set(value)

    @GObject.Property
    def needle_width(self) -> Optional[float]:
        return self._form.bn_needle_width.get()*1000

    @needle_width.setter
    def needle_width(self, value: Optional[float]) -> None:
        self._form.bn_needle_width.set(value)/1000
