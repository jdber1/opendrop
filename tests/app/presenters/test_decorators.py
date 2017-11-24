from abc import ABCMeta

import pytest

from opendrop.app.presenters import controlled_by, handler
from opendrop.app.presenters.BasePresenter import BasePresenter
from opendrop.utility.events import Event


def test_handler_tags_correctly():
    class SampleTestPresenter(BasePresenter):
        @handler("on_event0")
        def handle_event0(self):
            pass

        @handler("on_event1")
        def handle_event1(self):
            pass

    assert getattr(SampleTestPresenter.handle_event0, "_presenter_handler_tag") == "on_event0"
    assert getattr(SampleTestPresenter.handle_event1, "_presenter_handler_tag") == "on_event1"


@pytest.mark.skip
def test_controlled_by():
    class SampleTestPresenter(BasePresenter):
        @handler("on_event0")
        def handle_event0(self):
            pass

        @handler("on_event1")
        def handle_event1(self):
            pass

    class EmptyControllable(ABCMeta):
        pass

    Empty = EmptyControllable

    Decorated = controlled_by(SampleTestPresenter)(Empty)

    assert type(Decorated.on_event0) == Event and type(Decorated.on_event1) == Event
