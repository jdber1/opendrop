import asyncio
from typing import Any

from opendrop.app.presenters.ITimerExampleView import ITimerExampleView
from opendrop.mvp import handles
from opendrop.mvp.Presenter import Presenter


class TimerExamplePresenter(Presenter[Any, ITimerExampleView]):
    timer_on = False

    @handles('on_start_button_clicked')
    async def handle_start_button_clicked(self):
        if not self.timer_on:
            self.timer_on = True
            self.view.set_timer_countdown_mode(True)

            for i in range(int(self.view.get_timer_duration()), 0, -1):
                self.view.set_timer_countdown_value(i)
                await asyncio.sleep(1)

            self.view.set_timer_countdown_value(None)

            self.timer_on = False
            self.view.set_timer_countdown_mode(False)
