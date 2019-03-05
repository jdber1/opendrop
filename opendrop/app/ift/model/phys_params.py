import math
from typing import Optional

from opendrop.app.ift.model.analyser import IFTPhysicalParameters
from opendrop.utility.bindable import Bindable, BoxBindable, apply as bn_apply
from opendrop.utility.validation import validate, check_is_not_empty, check_is_positive, check_is_finite


class IFTPhysicalParametersFactory:
    def __init__(self):
        self.bn_inner_density = BoxBindable(None)  # type: Bindable[Optional[float]]
        self.bn_outer_density = BoxBindable(None)  # type: Bindable[Optional[float]]
        self.bn_needle_width = BoxBindable(None)  # type: Bindable[Optional[float]]
        self.bn_gravity = BoxBindable(None)  # type: Bindable[Optional[float]]

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

        self._errors = bn_apply(lambda *args: any(args),
            self.inner_density_err,
            self.outer_density_err,
            self.needle_width_err,
            self.gravity_err)

    @property
    def inner_density(self) -> float:
        return self.bn_inner_density.get()

    @inner_density.setter
    def inner_density(self, new_density: float) -> None:
        self.bn_inner_density.set(new_density)

    @property
    def outer_density(self) -> float:
        return self.bn_outer_density.get()

    @outer_density.setter
    def outer_density(self, new_density: float) -> None:
        self.bn_outer_density.set(new_density)

    @property
    def needle_width(self) -> float:
        return self.bn_needle_width.get()

    @needle_width.setter
    def needle_width(self, new_width: float) -> None:
        self.bn_needle_width.set(new_width)

    @property
    def gravity(self) -> float:
        return self.bn_gravity.get()

    @gravity.setter
    def gravity(self, new_gravity: float) -> None:
        self.bn_gravity.set(new_gravity)

    @property
    def has_errors(self) -> bool:
        return self._errors.get()

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
