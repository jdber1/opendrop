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
from typing import Tuple

from opendrop.utility.bindable import apply as bn_apply, BoxBindable
from opendrop.utility.validation import check_is_positive
from opendrop.utility.validation import validate, check_is_not_empty


class FigureOptions:
    def __init__(self, should_save: bool, dpi: int, size_w: float, size_h: float) -> None:
        self.bn_should_save = BoxBindable(should_save)
        self.bn_dpi = BoxBindable(dpi)
        self.bn_size_w = BoxBindable(size_w)
        self.bn_size_h = BoxBindable(size_h)

        # Validation

        self.dpi_err = validate(
            value=self.bn_dpi,
            checks=(check_is_not_empty,
                    check_is_positive),
            enabled=self.bn_should_save)
        self.size_w_err = validate(
            value=self.bn_size_w,
            checks=(check_is_not_empty,
                    check_is_positive),
            enabled=self.bn_should_save)
        self.size_h_err = validate(
            value=self.bn_size_h,
            checks=(check_is_not_empty,
                    check_is_positive),
            enabled=self.bn_should_save)

        self.errors = bn_apply(lambda *args: any(args), self.dpi_err, self.size_w_err, self.size_h_err)

    @property
    def size(self) -> Tuple[float, float]:
        return self.bn_size_w.get(), self.bn_size_h.get()
