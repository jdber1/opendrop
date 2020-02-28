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
import numpy as np


# Quantities are in SI units
def calculate_ift(
        inner_density: float,
        outer_density: float,
        bond_number: float,
        apex_radius: float,
        gravity: float
) -> float:
    delta_density = abs(inner_density - outer_density)
    gamma_ift = delta_density * gravity * apex_radius ** 2 / bond_number

    return gamma_ift


# Quantities are in SI units
def calculate_worthington(
        inner_density: float,
        outer_density: float,
        gravity: float,
        ift: float,
        volume: float,
        needle_width: float
) -> float:
    delta_density = abs(inner_density - outer_density)
    worthington_number = (delta_density * gravity * volume) / (np.pi * ift * needle_width)

    return worthington_number
