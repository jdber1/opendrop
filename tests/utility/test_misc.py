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
import sys

import pytest

from opendrop.utility.misc import recursive_load, get_classes_in_modules, clamp
from tests.samples import dummy_pkg


def test_get_classes_in_modules():
    clses = get_classes_in_modules(recursive_load(dummy_pkg), dummy_pkg.DummyClass)

    assert set(clses) == {
        dummy_pkg.DummyClass,
        dummy_pkg.module_a.MyFirstClass,
        dummy_pkg.subpkg.module_b.MySecondClass
    }


def test_recursive_load():
    modules = recursive_load(dummy_pkg)

    assert all(
        k in sys.modules
        for k in ['tests.samples.dummy_pkg.module_a', 'tests.samples.dummy_pkg.subpkg.module_b']
    )

    assert set(modules) == {
        dummy_pkg,
        dummy_pkg.module_a,
        dummy_pkg.subpkg,
        dummy_pkg.subpkg.module_b
    }


@pytest.mark.parametrize(
    '        x,     lower,    upper, expected', [
    (       -5,       -10,       -1,       -5),
    (        5,         1,       10,        5),
    (       11,         1,       10,       10),
    (       -5,         1,       10,        1),
    ( math.nan,         1,       10, math.nan),
    ( math.inf,         1,       10,       10),
    (-math.inf,         1,       10,        1),
    ( math.inf, -math.inf, math.inf, math.inf),
    (      123, -math.inf, math.inf,      123)])
def test_clamp(x, lower, upper, expected):
    if math.isnan(expected):
        assert math.isnan(clamp(x, lower, upper))
    else:
        assert clamp(x, lower, upper) == expected
