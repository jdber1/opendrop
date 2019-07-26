import asyncio
from typing import Optional

from opendrop.app.model import AppRootModel
from opendrop.mvp import EntryPoint
from .component import app_cs


class App(EntryPoint):
    root_component = app_cs

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self._loop = None  # type: Optional[asyncio.AbstractEventLoop]
        self._model = None  # type: Optional[AppRootModel]

    def start(self) -> None:
        from opendrop.vendor.glibcoro import glibcoro
        glibcoro.install()

        self._loop = asyncio.get_event_loop()
        self._model = AppRootModel(loop=self._loop)

        super().start(model=self._model)

        self._loop.run_forever()

    def _do_stop(self) -> None:
        self._loop.stop()
