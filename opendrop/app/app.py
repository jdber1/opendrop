import asyncio
import warnings
from abc import abstractmethod, ABC
from enum import Enum

from opendrop.gtk_specific.stack import StackModel
from opendrop.utility.speaker import Moderator, Speaker


class AppSpeakerID(Enum):
    MAIN_MENU = ('Main Menu',)
    IFT = ('Interfacial Tension Analysis',)
    CONAN = ('Contact Angle Analysis',)

    def __init__(self, header_title: str) -> None:
        self.header_title = header_title


class AppGUI(ABC):
    @abstractmethod
    def destroy(self) -> None:
        """Destroy the GUI."""


class AppGUIFactory(ABC):
    @abstractmethod
    def create(self, main_mod: Moderator, content_stack: StackModel) -> AppGUI:
        pass


class AppSpeakerFactory(ABC):
    @abstractmethod
    def set_content_stack(self, content_stack: StackModel) -> None:
        """Set `content_stack` as the main content stack model to be used by the speakers."""

    @abstractmethod
    def create_for_key(self, key: AppSpeakerID) -> Speaker:
        """Provide the speaker that will be identified by `key`"""


class App:
    def __init__(self, app_gui_factory: AppGUIFactory, speaker_factory: AppSpeakerFactory) -> None:
        self._loop = asyncio.get_event_loop()

        self._main_mod = Moderator()
        self._content_stack = StackModel()

        self._gui = app_gui_factory.create(self._main_mod, self._content_stack)

        speaker_factory.set_content_stack(self._content_stack)
        for key in AppSpeakerID:
            speaker = speaker_factory.create_for_key(key)
            if speaker is None:
                warnings.warn('No speaker created for key `{}`, ignoring.'.format(key))
                continue

            self._main_mod.add_speaker(key, speaker)

        self._main_mod.bn_active_speaker_key.on_changed.connect(self._hdl_main_mod_active_speaker_key_changed)

    def _hdl_main_mod_active_speaker_key_changed(self) -> None:
        if self._main_mod.active_speaker_key is None:
            self.destroy()

    def run(self) -> None:
        self._loop.create_task(self._main_mod.activate_speaker_by_key(AppSpeakerID.MAIN_MENU))
        self._loop.run_forever()

    def destroy(self) -> None:
        self._gui.destroy()
        self._loop.stop()
