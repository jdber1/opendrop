import sys

from opendrop.utility.misc import recursive_load, get_classes_in_modules
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
