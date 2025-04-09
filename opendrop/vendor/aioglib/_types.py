import asyncio
from typing import Any, Callable, Coroutine, Mapping


ExceptionHandler = Callable[[asyncio.AbstractEventLoop, Mapping], Any]
TaskFactory = Callable[[asyncio.AbstractEventLoop, Coroutine], asyncio.Task]
