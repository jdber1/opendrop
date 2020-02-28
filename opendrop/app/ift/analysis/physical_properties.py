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
import math
from typing import Optional

from opendrop.processing.ift import calculate_ift, calculate_worthington
from opendrop.utility.bindable import BoxBindable, Bindable
from .features import FeatureExtractor
from .young_laplace_fit import YoungLaplaceFitter


class PhysicalPropertiesCalculatorParams:
    def __init__(self) -> None:
        self.bn_inner_density = BoxBindable(math.nan)  # type: Bindable[Optional[float]]
        self.bn_outer_density = BoxBindable(math.nan)  # type: Bindable[Optional[float]]
        self.bn_needle_width = BoxBindable(math.nan)  # type: Bindable[Optional[float]]
        self.bn_gravity = BoxBindable(math.nan)  # type: Bindable[Optional[float]]


class PhysicalPropertiesCalculator:
    def __init__(
            self,
            features: FeatureExtractor,
            young_laplace_fit: YoungLaplaceFitter,
            params: PhysicalPropertiesCalculatorParams,
    ) -> None:
        self._extracted_features = features
        self._young_laplace_fit = young_laplace_fit

        self.params = params

        self.bn_interfacial_tension = BoxBindable(math.nan)
        self.bn_volume = BoxBindable(math.nan)
        self.bn_surface_area = BoxBindable(math.nan)
        self.bn_apex_radius = BoxBindable(math.nan)
        self.bn_worthington = BoxBindable(math.nan)

        features.bn_needle_width_px.on_changed.connect(self._recalculate)

        # Assume that bond number changes at the same time as other attributes
        young_laplace_fit.bn_bond_number.on_changed.connect(self._recalculate)

        params.bn_inner_density.on_changed.connect(self._recalculate)
        params.bn_outer_density.on_changed.connect(self._recalculate)
        params.bn_needle_width.on_changed.connect(self._recalculate)
        params.bn_gravity.on_changed.connect(self._recalculate)

        self._recalculate()

    def _recalculate(self) -> None:
        m_per_px = self._get_m_per_px()

        inner_density = self.params.bn_inner_density.get()
        outer_density = self.params.bn_outer_density.get()
        needle_width_m = self.params.bn_needle_width.get()
        gravity = self.params.bn_gravity.get()

        if inner_density is None or outer_density is None or needle_width_m is None or gravity is None:
            return

        bond_number = self._young_laplace_fit.bn_bond_number.get()
        apex_radius_px = self._young_laplace_fit.bn_apex_radius.get()

        apex_radius_m = m_per_px * apex_radius_px

        interfacial_tension = calculate_ift(
            inner_density=inner_density,
            outer_density=outer_density,
            bond_number=bond_number,
            apex_radius=apex_radius_m,
            gravity=gravity
        )

        volume_px3 = self._young_laplace_fit.bn_volume.get()
        volume_m3 = m_per_px**3 * volume_px3

        surface_area_px2 = self._young_laplace_fit.bn_surface_area.get()
        surface_area_m2 = m_per_px**2 * surface_area_px2

        worthington = calculate_worthington(
            inner_density=inner_density,
            outer_density=outer_density,
            gravity=gravity,
            ift=interfacial_tension,
            volume=volume_m3,
            needle_width=needle_width_m,
        )

        self.bn_interfacial_tension.set(interfacial_tension)
        self.bn_volume.set(volume_m3)
        self.bn_surface_area.set(surface_area_m2)
        self.bn_apex_radius.set(apex_radius_m)
        self.bn_worthington.set(worthington)

    def _get_m_per_px(self) -> float:
        needle_width_px = self._extracted_features.bn_needle_width_px.get()
        needle_width_m = self.params.bn_needle_width.get()

        if needle_width_px is None or needle_width_m is None:
            return math.nan

        return needle_width_m/needle_width_px
