import asyncio

import pytest

from opendrop.app.app import AppSpeakerID
from opendrop.app.main_menu.main_menu import MainMenuPresenter
from opendrop.utility.events import Event


class MockMainMenuView:
    def __init__(self):
        self.on_ift_btn_clicked = Event()
        self.on_conan_btn_clicked = Event()


class MockModerator:
    LOG_ACTIVATE_SPEAKER_BY_KEY = 'LOG_ACTIVATE_SPEAKER_BY_KEY'

    def __init__(self):
        self.log = []

    async def activate_speaker_by_key(self, key):
        self.log.append((self.LOG_ACTIVATE_SPEAKER_BY_KEY, key))


@pytest.mark.asyncio
async def test_main_menu_presenter_ift_btn_clicked():
    mock_view = MockMainMenuView()
    mock_mod = MockModerator()
    presenter = MainMenuPresenter(mock_mod, mock_view)

    mock_view.on_ift_btn_clicked.fire()
    await asyncio.sleep(0.01)
    assert mock_mod.log == [(MockModerator.LOG_ACTIVATE_SPEAKER_BY_KEY, AppSpeakerID.IFT)]


@pytest.mark.asyncio
async def test_main_menu_presenter_conan_btn_clicked():
    mock_view = MockMainMenuView()
    mock_mod = MockModerator()
    presenter = MainMenuPresenter(mock_mod, mock_view)

    mock_view.on_conan_btn_clicked.fire()
    await asyncio.sleep(0.01)
    assert mock_mod.log == [(MockModerator.LOG_ACTIVATE_SPEAKER_BY_KEY, AppSpeakerID.CONAN)]


@pytest.mark.asyncio
async def test_main_menu_presenter_destroy():
    mock_view = MockMainMenuView()
    mock_mod = MockModerator()
    presenter = MainMenuPresenter(mock_mod, mock_view)

    # Destroy the presenter
    presenter.destroy()

    # Make sure the button clicked events are ignored.
    mock_view.on_ift_btn_clicked.fire()
    await asyncio.sleep(0.01)
    assert mock_mod.log == []

    mock_view.on_conan_btn_clicked.fire()
    await asyncio.sleep(0.01)
    assert mock_mod.log == []
