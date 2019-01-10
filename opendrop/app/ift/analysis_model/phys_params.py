import math
from numbers import Number
from typing import Optional

from opendrop.iftcalc import IFTPhysicalParameters
from opendrop.utility.bindable.bindable import AtomicBindableVar, AtomicBindable, AtomicBindableAdapter


def _is_positive_float(x) -> bool:
    if isinstance(x, Number) and math.isfinite(x) and x > 0:
        return True
    else:
        return False


class IFTPhysicalParametersFactory:
    class Validator:
        def __init__(self, target: 'IFTPhysicalParametersFactory') -> None:
            self._target = target

            self.bn_inner_density_err_msg = AtomicBindableAdapter(self._get_inner_density_err_msg)
            self._target.bn_inner_density.on_changed.connect(self.bn_inner_density_err_msg.poke, immediate=True)

            self.bn_outer_density_err_msg = AtomicBindableAdapter(self._get_outer_density_err_msg)
            self._target.bn_outer_density.on_changed.connect(self.bn_outer_density_err_msg.poke, immediate=True)

            self.bn_needle_width_err_msg = AtomicBindableAdapter(self._get_needle_width_err_msg)
            self._target.bn_needle_width.on_changed.connect(self.bn_needle_width_err_msg.poke, immediate=True)

            self.bn_gravity_err_msg = AtomicBindableAdapter(self._get_gravity_err_msg)
            self._target.bn_gravity.on_changed.connect(self.bn_gravity_err_msg.poke, immediate=True)

        def _get_inner_density_err_msg(self) -> Optional[str]:
            inner_density = self._target.bn_inner_density.get()
            if inner_density is None:
                return 'Inner density cannot be empty'
            elif not _is_positive_float(inner_density):
                return 'Inner density must be greater than 0'

        def _get_outer_density_err_msg(self) -> Optional[str]:
            outer_density = self._target.bn_outer_density.get()
            if outer_density is None:
                return 'Outer density cannot be empty'
            elif not _is_positive_float(outer_density):
                return 'Outer density must be greater than 0'

        def _get_needle_width_err_msg(self) -> Optional[str]:
            needle_width = self._target.bn_needle_width.get()
            if needle_width is None:
                return 'Needle width cannot be empty'
            elif not _is_positive_float(needle_width):
                return 'Needle width must be greater than 0'

        def _get_gravity_err_msg(self) -> Optional[str]:
            gravity = self._target.bn_gravity.get()
            if gravity is None:
                return 'Gravity cannot be empty'
            elif not _is_positive_float(gravity):
                return 'Gravity must be greater than 0'

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
