from enum import Enum


class AppSpeakerID(Enum):
    MAIN_MENU = ('Main Menu',)
    IFT = ('Interfacial Tension Analysis',)
    CONAN = ('Contact Angle Analysis',)

    def __init__(self, header_title: str) -> None:
        self.header_title = header_title
