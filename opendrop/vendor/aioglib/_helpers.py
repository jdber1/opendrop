import asyncio
import functools
import inspect
import reprlib
import sys
import traceback
from typing import Optional, Any, Tuple, Iterable, Mapping
from types import FrameType

from . import constants


def format_callback_source(func: Any, args: Iterable) -> str:
    func_repr = format_callback(func, args, None)
    source = get_function_source(func)
    if source:
        func_repr += ' at {source[0]}:{source[1]}'.format(source=source)
    return func_repr


def format_args_and_kwargs(args, kwargs) -> str:
    """Format function arguments and keyword arguments.

    Special case for a single parameter: ('hello',) is formatted as ('hello').
    """
    # use reprlib to limit the length of the output
    items = []
    if args:
        items.extend(reprlib.repr(arg) for arg in args)
    if kwargs:
        items.extend('{}={}'.format(k, reprlib.repr(v)) for k, v in kwargs.items())
    return '({})'.format(', '.join(items))


def format_callback(func: Any, args: Iterable, kwargs: Optional[Mapping[str, Any]], suffix='') -> str:
    if isinstance(func, functools.partial):
        suffix = format_args_and_kwargs(args, kwargs) + suffix
        return format_callback(func.func, func.args, func.keywords, suffix)

    if hasattr(func, '__qualname__') and func.__qualname__:
        func_repr = func.__qualname__
    elif hasattr(func, '__name__') and func.__name__:
        func_repr = func.__name__
    else:
        func_repr = repr(func)

    func_repr += format_args_and_kwargs(args, kwargs)

    if suffix:
        func_repr += suffix

    return func_repr


def get_function_source(func: Any) -> Optional[Tuple[str, int]]:
    """Return a (filename, firstlineno) pair where `filename` is the name of the file where `func` was defined
    and `firstlineno` is the first line number of its definition. Return None if can't be determined."""
    func = inspect.unwrap(func)

    if inspect.isfunction(func):
        code = func.__code__
        return (code.co_filename, code.co_firstlineno)

    if isinstance(func, functools.partial):
        return get_function_source(func.func)

    if isinstance(func, functools.partialmethod):
        return get_function_source(func.func)

    return None


def extract_stack(f: Optional[FrameType] = None, limit: Optional[int] = None) -> traceback.StackSummary:
    """Replacement for traceback.extract_stack() that only does the necessary work for asyncio debug mode."""
    f = f if f is not None else sys._getframe(1)

    # Limit the amount of work to a reasonable amount, as extract_stack() can be called for each coroutine
    # and future in debug mode.
    limit = limit if limit is not None else constants.DEBUG_STACK_DEPTH

    stack = traceback.StackSummary.extract(
        traceback.walk_stack(f),
        limit=limit,
        lookup_lines=False,
        capture_locals=False,
    )

    stack.reverse()

    return stack


def get_future_loop(fut: asyncio.Future) -> asyncio.AbstractEventLoop:
    try:
        # Future.get_loop() was added in Python 3.7.
        return fut.get_loop()
    except AttributeError:
        # Access private '_loop' attribute in asyncio.Future implementation as fallback.
        return fut._loop
