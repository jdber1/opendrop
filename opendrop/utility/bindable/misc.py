from typing import Any

import numpy as np


def _general_purpose_equality_check(x: Any, y: Any) -> bool:
    try:
        return np.allclose(x, y, atol=0, equal_nan=True)
    except (ValueError, TypeError):
        # Use np.array_equal() in case x or y are `np.ndarray`s, in which case `bool(x == y)` will throw:
        #     ValueError: The truth value of an array with more than one element is ambiguous...
        # Even if x and y aren't both `np.ndarray`s, the implementation of np.array_equal() means that the result will
        # be identical to evaluating `x == y`, although this does not seem to be documented.
        return np.array_equal(x, y)
