from typing import Tuple

from opendrop.utility.bindable import apply as bn_apply, BoxBindable
from opendrop.utility.validation import check_is_positive
from opendrop.utility.validation import validate, check_is_not_empty


class FigureOptions:
    def __init__(self, should_save: bool, dpi: int, size_w: float, size_h: float) -> None:
        self.bn_should_save = BoxBindable(should_save)
        self.bn_dpi = BoxBindable(dpi)
        self.bn_size_w = BoxBindable(size_w)
        self.bn_size_h = BoxBindable(size_h)

        # Validation

        self.dpi_err = validate(
            value=self.bn_dpi,
            checks=(check_is_not_empty,
                    check_is_positive),
            enabled=self.bn_should_save)
        self.size_w_err = validate(
            value=self.bn_size_w,
            checks=(check_is_not_empty,
                    check_is_positive),
            enabled=self.bn_should_save)
        self.size_h_err = validate(
            value=self.bn_size_h,
            checks=(check_is_not_empty,
                    check_is_positive),
            enabled=self.bn_should_save)

        self.errors = bn_apply(lambda *args: any(args), self.dpi_err, self.size_w_err, self.size_h_err)

    @property
    def size(self) -> Tuple[float, float]:
        return self.bn_size_w.get(), self.bn_size_h.get()
