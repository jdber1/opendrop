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

from gi.repository import GObject


class PendantPhysicalParams:
    """Variables are in SI units."""

    def __init__(
            self,
            drop_density: float,
            continuous_density: float,
            needle_diameter: float,
            gravity: float
    ) -> None:
        self.drop_density = drop_density
        self.continuous_density = continuous_density
        self.needle_diameter = needle_diameter
        self.gravity = gravity


class PendantPhysicalParamsFactory(GObject.GObject):
    _drop_density: float = math.nan
    _continuous_density: float = math.nan
    _needle_diameter: float = math.nan
    _gravity: float = math.nan

    def create(self) -> PendantPhysicalParams:
        return PendantPhysicalParams(
            drop_density=self._drop_density,
            continuous_density=self._continuous_density,
            needle_diameter=self._needle_diameter,
            gravity=self._gravity,
        )

    @GObject.Signal
    def changed(self) -> None:
        """Emitted when parameters are changed."""

    @GObject.Property
    def drop_density(self) -> float:
        return self._drop_density

    @drop_density.setter
    def drop_density(self, density: float) -> None:
        self._drop_density = density
        self.changed.emit()

    @GObject.Property
    def continuous_density(self) -> float:
        return self._continuous_density

    @continuous_density.setter
    def continuous_density(self, density: float) -> None:
        self._continuous_density = density
        self.changed.emit()

    @GObject.Property
    def needle_diameter(self) -> float:
        return self._needle_diameter

    @needle_diameter.setter
    def needle_diameter(self, diameter: float) -> None:
        self._needle_diameter = diameter
        self.changed.emit()
    
    @GObject.Property
    def gravity(self) -> float:
        return self._gravity

    @gravity.setter
    def gravity(self, gravity: float) -> None:
        self._gravity = gravity
        self.changed.emit()
