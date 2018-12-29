import itertools
import math

import pytest

from opendrop.app.ift.analysis_model.phys_params import IFTPhysicalParametersFactory
from opendrop.app.ift.validation.phys_params_validator import IFTPhysicalParametersFactoryValidator


@pytest.mark.parametrize('inner_density, outer_density, needle_width, gravity', [
    (1, 2, 3, 4)
])
def test_validator_accepts_valid_data(inner_density, outer_density, needle_width, gravity):
    phys_params_factory = IFTPhysicalParametersFactory()
    validator = IFTPhysicalParametersFactoryValidator(phys_params_factory)

    phys_params_factory.bn_inner_density.set(inner_density)
    phys_params_factory.bn_outer_density.set(outer_density)
    phys_params_factory.bn_needle_width.set(needle_width)
    phys_params_factory.bn_gravity.set(gravity)

    assert validator.is_valid is True


@pytest.mark.parametrize('inner_density, outer_density, needle_width, gravity',
    set(itertools.chain(*(
        tuple(itertools.permutations([1, 1, 1, invalid_val], 4))
        for invalid_val in (None, -1, math.nan, math.inf, 0)
    )))
)
def test_validator_rejects_invalid_data(inner_density, outer_density, needle_width, gravity):
    phys_params_factory = IFTPhysicalParametersFactory()
    validator = IFTPhysicalParametersFactoryValidator(phys_params_factory)

    phys_params_factory.bn_inner_density.set(inner_density)
    phys_params_factory.bn_outer_density.set(outer_density)
    phys_params_factory.bn_needle_width.set(needle_width)
    phys_params_factory.bn_gravity.set(gravity)

    assert validator.is_valid is False
