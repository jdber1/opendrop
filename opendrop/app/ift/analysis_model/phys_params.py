import math
from typing import Optional

from opendrop.iftcalc.analyser import IFTPhysicalParameters
from opendrop.utility.bindable.bindable import AtomicBindableVar, AtomicBindable


class IFTPhysicalParametersFactory:
    class Validator:
        def __init__(self, target: 'IFTPhysicalParametersFactory') -> None:
            self._target = target

        def check_is_valid(self) -> bool:
            try:
                self._target.create_physical_parameters()
            except ValueError:
                return False

            return True

    def __init__(self):
        self.bn_inner_density = AtomicBindableVar(None)  # type: AtomicBindable[Optional[float]]
        self.bn_outer_density = AtomicBindableVar(None)  # type: AtomicBindable[Optional[float]]
        self.bn_needle_width = AtomicBindableVar(None)  # type: AtomicBindable[Optional[float]]
        self.bn_gravity = AtomicBindableVar(None)  # type: AtomicBindable[Optional[float]]

        self.validator = self.Validator(self)

    # Property adapters for atomic bindables
    inner_density = AtomicBindable.property_adapter(lambda self: self.bn_inner_density)
    outer_density = AtomicBindable.property_adapter(lambda self: self.bn_outer_density)
    needle_width = AtomicBindable.property_adapter(lambda self: self.bn_needle_width)
    gravity = AtomicBindable.property_adapter(lambda self: self.bn_gravity)

    def create_physical_parameters(self) -> IFTPhysicalParameters:
        inner_density = self.inner_density
        outer_density = self.outer_density
        needle_width = self.needle_width
        gravity = self.gravity

        for name, val in ({'inner_density': inner_density, 'outer_density': outer_density, 'needle_width': needle_width,
                          'gravity': gravity}).items():
            if val is None or math.isnan(val) or math.isinf(val) or (val <= 0):
                raise ValueError('{} must be a positive real float, currently `{}`'.format(name, val))

        return IFTPhysicalParameters(
            inner_density,
            outer_density,
            needle_width,
            gravity
        )
