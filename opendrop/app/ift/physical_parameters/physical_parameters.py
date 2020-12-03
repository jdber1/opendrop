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


from opendrop.app.ift.services.quantities import PendantPhysicalParamsFactory
from typing import Optional
from gi.repository import GObject
from injector import inject

from opendrop.appfw import component, Presenter

# The FloatEntry widget is referenced in the component template, import it now to make sure it's registered
# with the GLib type system.
from opendrop.widgets.float_entry import FloatEntry


@component(
    template_path='./physical_parameters.ui',
)
class IFTPhysicalParametersFormPresenter(Presenter):
    @inject
    def __init__(self, form: PendantPhysicalParamsFactory) -> None:
        self._form = form

        self._form_callback_ids = [
            self._form.connect('notify::drop-density', lambda *_: self.notify('inner-density')),
            self._form.connect('notify::continuous-density', lambda *_: self.notify('outer-density')),
            self._form.connect('notify::needle-diameter', lambda *_: self.notify('needle-width')),
            self._form.connect('notify::gravity', lambda *_: self.notify('gravity')),
        ]

    def destroy(self, *_) -> None:
        for callback_id in self._form_callback_ids:
            self._form.disconnect(callback_id)

    @GObject.Property
    def inner_density(self) -> Optional[float]:
        return self._form.drop_density

    @inner_density.setter
    def inner_density(self, density: Optional[float]) -> None:
        self._form.drop_density = density

    @GObject.Property
    def outer_density(self) -> Optional[float]:
        return self._form.continuous_density

    @outer_density.setter
    def outer_density(self, density: Optional[float]) -> None:
        self._form.continuous_density = density

    @GObject.Property
    def gravity(self) -> Optional[float]:
        return self._form.gravity

    @gravity.setter
    def gravity(self, gravity: Optional[float]) -> None:
        self._form.gravity = gravity

    @GObject.Property
    def needle_width(self) -> Optional[float]:
        needle_width_m = self._form.needle_diameter
        if needle_width_m is None:
            return None

        return needle_width_m*1000

    @needle_width.setter
    def needle_width(self, diameter_mm: Optional[float]) -> None:
        if diameter_mm is None:
            diameter_m = None
        else:
            diameter_m = diameter_mm/1000

        self._form.needle_diameter = diameter_m
