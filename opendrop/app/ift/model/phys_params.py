import math
from typing import Optional

from opendrop.app.ift.model.analyser import IFTPhysicalParameters
from opendrop.utility.bindable import bindable_function
from opendrop.utility.bindable.bindable import AtomicBindableVar, AtomicBindable
from opendrop.utility.validation import validate, check_is_not_empty, check_is_positive, check_is_finite


class IFTPhysicalParametersFactory:
    def __init__(self):
        self.bn_inner_density = AtomicBindableVar(None)  # type: AtomicBindable[Optional[float]]
        self.bn_outer_density = AtomicBindableVar(None)  # type: AtomicBindable[Optional[float]]
        self.bn_needle_width = AtomicBindableVar(None)  # type: AtomicBindable[Optional[float]]
        self.bn_gravity = AtomicBindableVar(None)  # type: AtomicBindable[Optional[float]]

        # Input validation
        self.inner_density_err = validate(
            value=self.bn_inner_density,
            checks=(check_is_not_empty,
                    check_is_finite))
        self.outer_density_err = validate(
            value=self.bn_outer_density,
            checks=(check_is_not_empty,
                    check_is_finite))
        self.needle_width_err = validate(
            value=self.bn_needle_width,
            checks=(check_is_not_empty,
                    check_is_positive))
        self.gravity_err = validate(
            value=self.bn_gravity,
            checks=(check_is_not_empty,
                    check_is_positive))

        self._errors = bindable_function(set.union)(
            self.inner_density_err,
            self.outer_density_err,
            self.needle_width_err,
            self.gravity_err)(AtomicBindableVar(False))

    # Property adapters for atomic bindables
    inner_density = AtomicBindable.property_adapter(lambda self: self.bn_inner_density)
    outer_density = AtomicBindable.property_adapter(lambda self: self.bn_outer_density)
    needle_width = AtomicBindable.property_adapter(lambda self: self.bn_needle_width)
    gravity = AtomicBindable.property_adapter(lambda self: self.bn_gravity)

    @property
    def has_errors(self) -> bool:
        return bool(self._errors.get())

    def create_physical_parameters(self) -> IFTPhysicalParameters:
        inner_density = self.inner_density
        outer_density = self.outer_density
        needle_width = self.needle_width
        gravity = self.gravity

        if inner_density is None or not math.isfinite(inner_density) or inner_density < 0:
            raise ValueError('inner_density must be a non-negative real float, currently `{}`'.format(inner_density))

        if outer_density is None or not math.isfinite(outer_density) or outer_density < 0:
            raise ValueError('outer_density must be a non-negative real float, currently `{}`'.format(outer_density))

        if needle_width is None or not math.isfinite(needle_width) or needle_width <= 0:
            raise ValueError('needle_width must be a positive real float, currently `{}`'.format(needle_width))

        if gravity is None or not math.isfinite(gravity) or gravity <= 0:
            raise ValueError('needle_width must be a positive real float, currently `{}`'.format(gravity))

        return IFTPhysicalParameters(
            inner_density,
            outer_density,
            needle_width,
            gravity)
