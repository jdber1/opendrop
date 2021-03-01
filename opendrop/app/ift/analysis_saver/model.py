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


from pathlib import Path
from typing import Optional

from opendrop.app.common.analysis_saver.figure_options import FigureOptions
from opendrop.utility.bindable import VariableBindable
from opendrop.utility.bindable.typing import Bindable


class IFTAnalysisSaverOptions:
    def __init__(self) -> None:
        self.bn_save_dir_parent = VariableBindable(None)  # type: Bindable[Optional[Path]]
        self.bn_save_dir_name = VariableBindable('')

        self.drop_residuals_figure_opts = FigureOptions(
            should_save=False,
            dpi=300,
            size_w=10,
            size_h=10
        )

        self.ift_figure_opts = FigureOptions(
            should_save=False,
            dpi=300,
            size_w=15,
            size_h=9
        )

        self.volume_figure_opts = FigureOptions(
            should_save=False,
            dpi=300,
            size_w=15,
            size_h=9
        )

        self.surface_area_figure_opts = FigureOptions(
            should_save=False,
            dpi=300,
            size_w=15,
            size_h=9
        )

    @property
    def save_root_dir(self) -> Path:
        return self.bn_save_dir_parent.get() / self.bn_save_dir_name.get()
