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
from typing import Optional

from gi.repository import GObject

from opendrop.app.ift.analysis import IFTDropAnalysis
from opendrop.appfw import Presenter, component, install


@component(
    template_path='./parameters.ui',
)
class IFTReportOverviewParametersPresenter(Presenter):
    _analysis = None
    _event_connections = ()

    @install
    @GObject.Property
    def analysis(self) -> Optional[IFTDropAnalysis]:
        return self._analysis

    @analysis.setter
    def analysis(self, value: Optional[IFTDropAnalysis]) -> None:
        for conn in self._event_connections:
            conn.disconnect()
        self._event_connections = ()

        self._analysis = value

        if self._analysis is None:
            return

        self._event_connections = (
            self._analysis.bn_interfacial_tension.on_changed.connect(lambda: self.notify('ift'), weak_ref=False),
            self._analysis.bn_volume.on_changed.connect(lambda: self.notify('volume'), weak_ref=False),
            self._analysis.bn_surface_area.on_changed.connect(lambda: self.notify('surface-area'), weak_ref=False),
            self._analysis.bn_worthington.on_changed.connect(lambda: self.notify('worthington'), weak_ref=False),
            self._analysis.bn_bond_number.on_changed.connect(lambda: self.notify('bond-number'), weak_ref=False),
            self._analysis.bn_apex_coords_px.on_changed.connect(lambda: self.notify('apex-coordinates'), weak_ref=False),
            self._analysis.bn_rotation.on_changed.connect(lambda: self.notify('image-angle'), weak_ref=False),
        )

        self.notify('ift')
        self.notify('volume')
        self.notify('surface-area')
        self.notify('worthington')
        self.notify('bond-number')
        self.notify('apex-coordinates')
        self.notify('image-angle')

    @GObject.Property(type=str)
    def ift(self) -> str:
        value = self._analysis.bn_interfacial_tension.get()
        text = '{:#.3g}'.format(value * 1e3)
        return text

    @GObject.Property(type=str)
    def volume(self) -> str:
        value = self._analysis.bn_volume.get()
        text = '{:#.3g}'.format(value * 1e9)
        return text
    
    @GObject.Property(type=str)
    def surface_area(self) -> str:
        value = self._analysis.bn_surface_area.get()
        text = '{:#.3g}'.format(value * 1e6)
        return text
    
    @GObject.Property(type=str)
    def worthington(self) -> str:
        value = self._analysis.bn_worthington.get()
        text = '{:#.3g}'.format(value)
        return text

    @GObject.Property(type=str)
    def bond_number(self) -> str:
        value = self._analysis.bn_bond_number.get()
        text = '{:#.3g}'.format(value)
        return text

    @GObject.Property(type=str)
    def apex_coordinates(self) -> str:
        value = self._analysis.bn_apex_coords_px.get()
        text = '({:.0f}, {:.0f})'.format(value[0], value[1])
        return text

    @GObject.Property(type=str)
    def image_angle(self) -> str:
        value = self._analysis.bn_rotation.get()
        text = '{:#.2g}°'.format(math.degrees(value))
        return text

    def destroy(self, *_) -> None:
        # Unbind analysis.
        self.analysis = None
