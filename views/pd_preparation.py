from customtkinter import *
import customtkinter as ctk

class PdPreparation(CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.label = CTkLabel(self, text="Dynamic Content Goes Here", text_color="black")
        self.label.pack(pady=20)
        
        # Add other widgets for dynamic content as needed
        self.image_source_button = CTkButton(self, text="Preparation", width=150, height=40)
        self.image_source_button.pack(pady=10)
