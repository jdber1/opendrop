from typing import Any
import numbers

import numpy as np


def _general_purpose_equality_check(x: Any, y: Any) -> bool:
    if isinstance(x, numbers.Number) and isinstance(y, numbers.Number):
        return np.allclose(x, y, atol=0, equal_nan=True)
    elif isinstance(x, np.ndarray) or isinstance(y, np.ndarray):
        return np.array_equal(x, y)
    else:
        try:
            if len(x) != len(y):
                return False

            return all(
                _general_purpose_equality_check(xi, yi)
                for xi, yi in zip(x, y)
            )
        except TypeError:
            return x == y
