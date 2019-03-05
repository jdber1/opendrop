import asyncio
from enum import Enum

import pytest

from opendrop.app.app import AppSpeakerID
from opendrop.app.header import HeaderPresenter
from opendrop.utility.simplebindable import BoxBindable
from opendrop.utility.events import Event
from opendrop.utility.speaker import Moderator, Speaker


class MockHeaderView:
    def __init__(self):
        self.bn_header_title = BoxBindable('')
        self.bn_return_to_menu_btn_visible = BoxBindable(True)

        self.on_return_to_menu_btn_clicked = Event()


class MockModerator:
    LOG_ACTIVATE_SPEAKER_BY_KEY = 'LOG_ACTIVATE_SPEAKER_BY_KEY'

    def __init__(self):
        super().__init__()
        self.bn_active_speaker_key = BoxBindable(None)

        self.log = []

    async def activate_speaker_by_key(self, key):
        self.log.append((self.LOG_ACTIVATE_SPEAKER_BY_KEY, key))
        self.bn_active_speaker_key.set(key)


class MockAppSpeakerID(Enum):
    MY_SPEAKER0 = ('My Speaker 0',)
    MY_SPEAKER1 = ('My Speaker 1',)

    def __init__(self, header_title: str) -> None:
        self.header_title = header_title


@pytest.mark.asyncio
async def test_header_presenter_on_return_menu_btn_clicked():
    mock_view = MockHeaderView()
    mock_mod = MockModerator()
    presenter = HeaderPresenter(mock_mod, mock_view)

    mock_view.on_return_to_menu_btn_clicked.fire()
    await asyncio.sleep(0.01)

    assert mock_mod.log == [(MockModerator.LOG_ACTIVATE_SPEAKER_BY_KEY, AppSpeakerID.MAIN_MENU)]


@pytest.mark.asyncio
async def test_header_presenter_propagates_header_title():
    mock_view = MockHeaderView()
    mod = Moderator()
    presenter = HeaderPresenter(mod, mock_view)

    mod.add_speaker(MockAppSpeakerID.MY_SPEAKER0, Speaker())
    mod.add_speaker(MockAppSpeakerID.MY_SPEAKER1, Speaker())

    await mod.activate_speaker_by_key(MockAppSpeakerID.MY_SPEAKER0)
    assert mock_view.bn_header_title.get() == MockAppSpeakerID.MY_SPEAKER0.header_title

    await mod.activate_speaker_by_key(MockAppSpeakerID.MY_SPEAKER1)
    assert mock_view.bn_header_title.get() == MockAppSpeakerID.MY_SPEAKER1.header_title

    await mod.activate_speaker_by_key(None)
    assert mock_view.bn_header_title.get() == ''


@pytest.mark.asyncio
async def test_header_presenter_syncs_header_title():
    mock_view = MockHeaderView()
    mod = Moderator()
    mod.add_speaker(MockAppSpeakerID.MY_SPEAKER0, Speaker())
    await mod.activate_speaker_by_key(MockAppSpeakerID.MY_SPEAKER0)

    presenter = HeaderPresenter(mod, mock_view)

    assert mock_view.bn_header_title.get() == MockAppSpeakerID.MY_SPEAKER0.header_title


@pytest.mark.asyncio
async def test_header_presenter_propagates_return_to_menu_btn_visible():
    mock_view = MockHeaderView()
    mod = Moderator()
    presenter = HeaderPresenter(mod, mock_view)

    mod.add_speaker(AppSpeakerID.MAIN_MENU, Speaker())
    mod.add_speaker(MockAppSpeakerID.MY_SPEAKER0, Speaker())

    await mod.activate_speaker_by_key(MockAppSpeakerID.MY_SPEAKER0)
    assert mock_view.bn_return_to_menu_btn_visible.get() is True

    await mod.activate_speaker_by_key(AppSpeakerID.MAIN_MENU)
    assert mock_view.bn_return_to_menu_btn_visible.get() is False


@pytest.mark.asyncio
async def test_header_presenter_syncs_return_to_menu_btn_visible():
    # Test if initial speaker is main menu
    mock_view = MockHeaderView()
    mod = Moderator()
    mod.add_speaker(AppSpeakerID.MAIN_MENU, Speaker())
    await mod.activate_speaker_by_key(AppSpeakerID.MAIN_MENU)

    presenter = HeaderPresenter(mod, mock_view)

    assert mock_view.bn_return_to_menu_btn_visible.get() is False

    # Test if initial speaker is not main menu
    mock_view = MockHeaderView()
    mod = Moderator()
    mod.add_speaker(MockAppSpeakerID.MY_SPEAKER0, Speaker())
    await mod.activate_speaker_by_key(MockAppSpeakerID.MY_SPEAKER0)

    presenter = HeaderPresenter(mod, mock_view)

    assert mock_view.bn_return_to_menu_btn_visible.get() is True


@pytest.mark.asyncio
async def test_header_presenter_destroy_ignores_on_return_to_menu_btn_clicked():
    mock_view = MockHeaderView()
    mock_mod = MockModerator()
    presenter = HeaderPresenter(mock_mod, mock_view)
    presenter.destroy()

    mock_view.on_return_to_menu_btn_clicked.fire()
    await asyncio.sleep(0.01)
    assert mock_mod.log == []


@pytest.mark.asyncio
async def test_header_presenter_destroy_ignores_propagate_header_title():
    mock_view = MockHeaderView()
    mod = Moderator()
    presenter = HeaderPresenter(mod, mock_view)

    mod.add_speaker(MockAppSpeakerID.MY_SPEAKER0, Speaker())
    mod.add_speaker(MockAppSpeakerID.MY_SPEAKER1, Speaker())

    presenter.destroy()

    await mod.activate_speaker_by_key(MockAppSpeakerID.MY_SPEAKER0)
    assert mock_view.bn_header_title.get() == ''

    await mod.activate_speaker_by_key(MockAppSpeakerID.MY_SPEAKER1)
    assert mock_view.bn_header_title.get() == ''


@pytest.mark.asyncio
async def test_header_presenter_destroy_ignores_propagate_return_to_menu_btn_visible():
    mock_view = MockHeaderView()
    mod = Moderator()
    presenter = HeaderPresenter(mod, mock_view)

    mod.add_speaker(AppSpeakerID.MAIN_MENU, Speaker())
    mod.add_speaker(MockAppSpeakerID.MY_SPEAKER1, Speaker())

    presenter.destroy()

    await mod.activate_speaker_by_key(AppSpeakerID.MAIN_MENU)
    assert mock_view.bn_return_to_menu_btn_visible.get() is True
