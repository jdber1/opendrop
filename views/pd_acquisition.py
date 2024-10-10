from customtkinter import *
import customtkinter as ctk

class PdAcquisition(CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        self.image_source_button = CTkButton(self, text="Filesystem", width=150, height=40)
        self.image_source_button.pack(pady=10)

        self.choose_files_button = CTkButton(self, text="Choose File(s)", width=150, height=40)
        self.choose_files_button.pack(pady=10)
