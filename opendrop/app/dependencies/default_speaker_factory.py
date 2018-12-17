from typing import Optional

from opendrop.app.app import AppSpeakerFactory, AppSpeakerID
from opendrop.app.conan.conan import ConanSpeaker
from opendrop.app.ift.ift import IFTSpeaker
from opendrop.app.main_menu.main_menu import MainMenuSpeaker
from opendrop.component.stack import StackModel
from opendrop.utility.speaker import Speaker


class DefaultAppSpeakersFactory(AppSpeakerFactory):
    def __init__(self) -> None:
        self._content_stack = None  # type: Optional[StackModel]

    def set_content_stack(self, content_stack: StackModel) -> None:
        self._content_stack = content_stack

    def create_for_key(self, key: AppSpeakerID) -> Speaker:
        if key is AppSpeakerID.MAIN_MENU:
            return self.create_main_menu()
        elif key is AppSpeakerID.IFT:
            return self.create_ift()
        elif key is AppSpeakerID.CONAN:
            return self.create_conan()

    def create_main_menu(self) -> MainMenuSpeaker:
        if self._content_stack is None:
            raise ValueError('content_model dependency not provided')

        return MainMenuSpeaker(self._content_stack)

    def create_ift(self) -> IFTSpeaker:
        if self._content_stack is None:
            raise ValueError('content_model dependency not provided')

        return IFTSpeaker(self._content_stack)

    def create_conan(self) -> ConanSpeaker:
        if self._content_stack is None:
            raise ValueError('content_model dependency not provided')

        return ConanSpeaker(self._content_stack)
