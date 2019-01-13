from opendrop.utility.bindable.bindable import AtomicBindableVar
from opendrop.utility.option import MutuallyExclusiveOptions


def test_mutually_exclusive_options_normal_usage():
    options = (AtomicBindableVar(False), AtomicBindableVar(False), AtomicBindableVar(False))
    MutuallyExclusiveOptions(options)
    assert all(option.get() is False for option in options)

    options[0].set(True)

    options[1].set(True)
    assert options[0].get() is False

    options[2].set(True)
    assert options[1].get() is False

    options[0].set(True)
    assert options[2].get() is False
