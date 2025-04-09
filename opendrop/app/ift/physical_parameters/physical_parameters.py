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
            self._form.connect('notify::drop-density', lambda *_: self.notify('drop-density')),
            self._form.connect('notify::continuous-density', lambda *_: self.notify('continuous-density')),
            self._form.connect('notify::needle-diameter', lambda *_: self.notify('needle-diameter')),
            self._form.connect('notify::pixel-scale', lambda *_: self.notify('pixel-scale')),
            self._form.connect('notify::gravity', lambda *_: self.notify('gravity')),
        ]

    def destroy(self, *_) -> None:
        for callback_id in self._form_callback_ids:
            self._form.disconnect(callback_id)

    @GObject.Property
    def drop_density(self) -> Optional[float]:
        return self._form.drop_density

    @drop_density.setter
    def drop_density(self, density: Optional[float]) -> None:
        self._form.drop_density = density

    @GObject.Property
    def continuous_density(self) -> Optional[float]:
        return self._form.continuous_density

    @continuous_density.setter
    def continuous_density(self, density: Optional[float]) -> None:
        self._form.continuous_density = density

    @GObject.Property
    def gravity(self) -> Optional[float]:
        return self._form.gravity

    @gravity.setter
    def gravity(self, gravity: Optional[float]) -> None:
        self._form.gravity = gravity

    @GObject.Property
    def needle_diameter(self) -> Optional[float]:
        needle_diameter_m = self._form.needle_diameter
        if needle_diameter_m is None:
            return None

        # Return needle in millimeters.
        return needle_diameter_m * 1000

    @needle_diameter.setter
    def needle_diameter(self, diameter_mm: Optional[float]) -> None:
        if diameter_mm is None:
            diameter_m = None
        else:
            diameter_m = diameter_mm/1000

        self._form.needle_diameter = diameter_m

    @GObject.Property
    def pixel_scale(self) -> Optional[float]:
        pixel_per_m = self._form.pixel_scale
        if pixel_per_m is None:
            return None

        # Return pixel per millimeters.
        return pixel_per_m * 1000

    @pixel_scale.setter
    def pixel_scale(self, pixel_per_mm: Optional[float]) -> None:
        if pixel_per_mm is None:
            pixel_per_m = None
        else:
            pixel_per_m = pixel_per_mm*1000

        self._form.pixel_scale = pixel_per_m
