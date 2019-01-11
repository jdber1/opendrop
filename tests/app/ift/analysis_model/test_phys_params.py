import itertools
import math

import pytest

from opendrop.app.ift.analysis_model.phys_params import IFTPhysicalParametersFactory


def _is_valid_data(inner_density, outer_density, needle_width, gravity):
    if None in (inner_density, outer_density, needle_width, gravity):
        return False
    if not all(map(math.isfinite, (inner_density, outer_density, needle_width, gravity))):
        return False
    if inner_density < 0:
        return False
    if outer_density < 0:
        return False
    if needle_width <= 0:
        return False
    if gravity <= 0:
        return False

    return True


@pytest.mark.parametrize('inner_density, outer_density, needle_width, gravity', [
    (1, 2, 3, 4)
])
def test_phys_params_factory_create_with_valid_data(inner_density, outer_density, needle_width, gravity):
    phys_params_factory = IFTPhysicalParametersFactory()
    phys_params_factory.bn_inner_density.set(inner_density)
    phys_params_factory.bn_outer_density.set(outer_density)
    phys_params_factory.bn_needle_width.set(needle_width)
    phys_params_factory.bn_gravity.set(gravity)

    phys_params = phys_params_factory.create_physical_parameters()

    assert phys_params.inner_density == inner_density
    assert phys_params.outer_density == outer_density
    assert phys_params.needle_width == needle_width
    assert phys_params.gravity == gravity


@pytest.mark.parametrize('inner_density, outer_density, needle_width, gravity',
    set(filter(lambda x: not _is_valid_data(*x), itertools.chain(*(
        tuple(itertools.permutations([1, 1, 1, invalid_val], 4))
        for invalid_val in (None, -1, math.nan, math.inf, 0))))))
def test_phys_params_factory_create_with_invalid_data(inner_density, outer_density, needle_width, gravity):
    phys_params_factory = IFTPhysicalParametersFactory()
    phys_params_factory.bn_inner_density.set(inner_density)
    phys_params_factory.bn_outer_density.set(outer_density)
    phys_params_factory.bn_needle_width.set(needle_width)
    phys_params_factory.bn_gravity.set(gravity)

    # Should fail to create since some fields have invalid values.
    with pytest.raises(ValueError):
        phys_params_factory.create_physical_parameters()


# Test validation

@pytest.mark.parametrize('inner_density, outer_density, needle_width, gravity', [
    (1, 2, 3, 4)
])
def test_validator_accepts_valid_data(inner_density, outer_density, needle_width, gravity):
    phys_params_factory = IFTPhysicalParametersFactory()

    phys_params_factory.bn_inner_density.set(inner_density)
    phys_params_factory.bn_outer_density.set(outer_density)
    phys_params_factory.bn_needle_width.set(needle_width)
    phys_params_factory.bn_gravity.set(gravity)

    assert phys_params_factory.validator.check_is_valid() is True


@pytest.mark.parametrize('inner_density, outer_density, needle_width, gravity',
    set(filter(lambda x: not _is_valid_data(*x), itertools.chain(*(
        tuple(itertools.permutations([1, 1, 1, invalid_val], 4))
        for invalid_val in (None, -1, math.nan, math.inf, 0))))))
def test_validator_rejects_invalid_data(inner_density, outer_density, needle_width, gravity):
    phys_params_factory = IFTPhysicalParametersFactory()

    phys_params_factory.bn_inner_density.set(inner_density)
    phys_params_factory.bn_outer_density.set(outer_density)
    phys_params_factory.bn_needle_width.set(needle_width)
    phys_params_factory.bn_gravity.set(gravity)

    assert phys_params_factory.validator.check_is_valid() is False
