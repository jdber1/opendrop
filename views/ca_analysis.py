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

        self._setup_ui()
        self.progress_var = StringVar(value="0")
        self.thread = None

    def _setup_ui(self):
        """Set up the UI components."""
        self.label = CTkLabel(self, text="Processing...")
        self.label.pack(pady=20)

        self.progress_label = CTkLabel(self, textvariable=self.progress_var)
        self.progress_label.pack(pady=20)

        self.start_button = CTkButton(self, text="Start Processing", command=self.start_processing)
        self.start_button.pack(pady=20)

    def start_processing(self):
        """Start data processing in a separate thread."""
        self.label.configure(text="Processing started...")
        self.progress_var.set("0% completed")
        
        # Create and start a new thread for processing
        self.thread = threading.Thread(target=self.process_data)
        self.thread.start()

        # Update UI periodically
        self.update_ui()

    def process_data(self):
        """Simulate data processing."""
        for i in range(1, 101):  # Simulate processing 100 units of work
            time.sleep(0.1)  # Simulate time-consuming task
            self.progress_var.set(f"{i}% completed")

    def update_ui(self):
        """Update the UI while processing."""
        if self.thread.is_alive():
            self.after(100, self.update_ui)  # Check again in 100 ms
        else:
            self.on_processing_complete()

    def on_processing_complete(self):
        """Handle completion of data processing."""
        self.label.configure(text="Processing completed!")