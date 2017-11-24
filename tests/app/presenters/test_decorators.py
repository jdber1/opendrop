from abc import ABCMeta

import pytest

from opendrop.app.presenters.metadata import controlled_by, handles
from opendrop.app.presenters.BasePresenter import BasePresenter
from opendrop.utility.events import Event


def test_controlled_by_creates_events():
    class SampleTestPresenter(BasePresenter):
        @handles("on_event0")
        def handle_event0(self):
            pass

        @handles("on_event1")
        def handle_event1(self):
            pass

    class EmptyControllable():
        pass

    Empty = EmptyControllable

    Decorated = controlled_by(SampleTestPresenter)(Empty)

    d1 = Decorated()
    d2 = Decorated()

    assert (
        d1.on_event0 != d2.on_event0 and
        d1.on_event1 != d2.on_event1 and
        all(isinstance(getattr(di, event_name), Event) for event_name in ['on_event0', 'on_event1'] for di in [d1, d2])
    )