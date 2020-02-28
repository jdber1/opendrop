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


import gc
import itertools
import weakref
from unittest.mock import Mock

import pytest

from opendrop.utility.events import Event
from opendrop.utility.bindable.apply import apply


class TestApply:
    @pytest.fixture(autouse=True)
    def fixture(self):
        self.my_function = Mock()
        self.bn_args = [MockBindable(), MockBindable()]
        self.bn_kwargs = {'abc': MockBindable(), 'def': MockBindable()}
        self.result = apply(self.my_function, *self.bn_args, **self.bn_kwargs)

    def test_result_changes_as_arguments_change(self):
        result_on_changed_callback = Mock()
        self.result.on_changed.connect(result_on_changed_callback)

        for bn_arg in itertools.chain(self.bn_args, self.bn_kwargs.values()):
            result_on_changed_callback.reset_mock()
            bn_arg.poke()
            result_on_changed_callback.assert_called_once_with()

    def test_result_value(self):
        self.my_function.assert_not_called()
        result_value = self.result.get()
        assert result_value == self.my_function.return_value

        args = [bn.get() for bn in self.bn_args]
        kwargs = {key: bn.get() for key, bn in self.bn_kwargs.items()}

        self.my_function.assert_called_once_with(*args, **kwargs)

    def test_result_set(self):
        # Can't set the value of result
        with pytest.raises(NotImplementedError):
            self.result.set(object())

    def test_no_indirect_references_to_result(self):
        result_wr = weakref.ref(self.result)
        del self.result
        gc.collect()

        assert result_wr() is None


class MockBindable:
    def __init__(self):
        self.on_changed = Event()
        self.get = Mock()
        self.set = Mock()

    def poke(self) -> None:
        self.on_changed.fire()

    def reset(self):
        self.get.reset_mock()
        self.set.reset_mock()
