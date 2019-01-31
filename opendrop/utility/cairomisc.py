from contextlib import contextmanager
from typing import Any, Generator

import cairo


@contextmanager
def cairo_saved(cr: cairo.Context) -> Generator[None, Any, None]:
    cr.save()
    try:
        yield
    finally:
        cr.restore()
