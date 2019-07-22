import math
from typing import Optional

from gi.repository import GObject

from opendrop.widgets.validated_entry import ValidatedEntry


class FloatEntry(ValidatedEntry):
    # TODO: Remove this code duplication with IntegerEntry
    _lower = None  # type: Optional[int]
    _upper = None  # type: Optional[int]
    _default = None  # type: Optional[int]

    @GObject.Property
    def lower(self) -> Optional[int]:
        return self._lower

    @lower.setter
    def lower(self, value: Optional[int]) -> None:
        self._lower = value

    @GObject.Property
    def upper(self) -> Optional[int]:
        return self._upper

    @upper.setter
    def upper(self, value: Optional[int]) -> None:
        self._upper = value

    @GObject.Property
    def default(self) -> Optional[int]:
        return self._default

    @default.setter
    def default(self, value: Optional[int]) -> None:
        self._default = value

    def restrict(self, value: Optional[int]) -> Optional[int]:
        value = self.default if value is None else value
        if value is None:
            return None

        if self.lower is not None:
            value = max(value, self.lower)

        if self.upper is not None:
            value = min(value, self.upper)

        return value

    def validate(self, text: str) -> bool:
        if text == '':
            return True

        if self.upper is not None and self.upper < 0 and text[0] == '+':
            return False
        elif self.lower is not None and self.lower >= 0 and text[0] == '-':
            return False

        try:
            v = self.t_from_str(text)
        except ValueError:
            return False

        if v is not None and math.isnan(v):
            return False

        return True

    def t_from_str(self, text: str) -> Optional[float]:
        if text == '':
            return None

        if text in ('+', '-', '.'):
            return None

        if text.count('e') == 1:
            if text.endswith('e'):
                return self.t_from_str(text[:-1])

            if text.endswith('e+') or text.endswith('e-'):
                return self.t_from_str(text[:-2])

            if text.startswith('e'):
                try:
                    int(text[1:])
                except ValueError:
                    raise
                else:
                    return None

        return float(text)

    def str_from_t(self, value: Optional[float]) -> str:
        if value is None or math.isnan(value):
            return ''

        precision = self.props.width_chars
        precision = max(precision - 3, 1)

        return format(float(value), '.{}g'.format(precision))
