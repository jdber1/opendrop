from customtkinter import *
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import time

from utils.config import *
from utils.validators import *
from .component.option_menu import OptionMenu
from .component.integer_entry import IntegerEntry

class CaAnalysis(CTkFrame):
    def __init__(self, parent, user_input_data, **kwargs):
        super().__init__(parent, **kwargs)  
        self.user_input_data = user_input_data

        self.output = []

        self.setup_ui()

    def setup_ui(self):
        """Set up the UI components."""
        self.label = CTkLabel(self, text="Processing...")
        self.label.pack(pady=20)

        self.updatingLabel = CTkLabel(self, text="No result yet")
        self.updatingLabel.pack(pady=20)

    def receive_output(self , extracted_data):
        self.output.append(extracted_data)

        self.updatingLabel.configure(text="processed: " + str(len(self.output)))

        #print("Received extracted data:", extracted_data)