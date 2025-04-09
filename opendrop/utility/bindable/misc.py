from typing import Any
import numbers

import numpy as np


def _general_purpose_equality_check(
        x: Any,
        y: Any,
        x_parent: Any = None,
        y_parent: Any = None,
) -> bool:
    if x is y:
        return True

    if x is None or y is None:
        return x is y
    elif isinstance(x, bool) or isinstance(y, bool):
        return x is y
    elif isinstance(x, np.ndarray) or isinstance(y, np.ndarray):
        return np.array_equal(x, y)
    elif isinstance(x, numbers.Number) and isinstance(y, numbers.Number):
        return np.allclose(x, y, atol=0, equal_nan=True)
    elif isinstance(x, str) or isinstance(y, str):
        return x == y
    elif x is not x_parent and y is not y_parent:
        try:
            if len(x) != len(y):
                return False

            return all(
                _general_purpose_equality_check(xi, yi, x, y)
                for xi, yi in zip(x, y)
            )
        except TypeError:
            return x == y
    else:
        return x == y
