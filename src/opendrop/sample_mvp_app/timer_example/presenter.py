import asyncio
from typing import Any

from opendrop.mvp.Presenter import Presenter
from opendrop.sample_mvp_app.timer_example.iview import ITimerExampleView


class TimerExamplePresenter(Presenter[Any, ITimerExampleView]):
    timer_on = False

    def setup(self):
        self.view.events.on_start_button_clicked.connect(self.handle_start_button_clicked)
        self.view.events.on_request_close.connect(self.handle_view_request_close)

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

    def handle_view_request_close(self):
        self.view.spawn(self.view.PREVIOUS)
        self.view.close()
