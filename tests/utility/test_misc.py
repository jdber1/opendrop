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
