import signal
import sys

import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

class MainWindow(ctk.CTk):
    def __init__(self, open_ift_window, open_ca_window):
        super().__init__()
        self.title("Main Window")
        self.geometry("800x400")

        # Define a function to handle the SIGINT signal (Ctrl+C)
        def signal_handler(sig, frame):
            print("Exiting...")
            try:
                self.destroy()  # Close the application
            except tk.TclError:
                print("Application already destroyed.")
            sys.exit(0)
        # Attach the signal handler to SIGINT
        signal.signal(signal.SIGINT, signal_handler)

        # Display title
        title_label = ctk.CTkLabel(
            self, text="OpenDrop2", font=("Helvetica", 48))
        title_label.pack(pady=50)

        # Create main functionality buttons
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=50)

        # Bind the buttons to the same functions as in the old code
        self.create_button(
            button_frame, "Interfacial Tension", open_ift_window, 0)
        self.create_button(button_frame, "Contact Angle", open_ca_window, 1)

        # Add information button at bottom-right corner
        info_button = ctk.CTkButton(self, text="❗", command=self.show_info_popup, font=(
            "Arial", 12, "bold"), fg_color="white", text_color="red", width=5)
        # Positioned in the bottom-right corner
        info_button.place(relx=1.0, rely=1.0, anchor='se', x=-10, y=-10)

        self.mainloop()

    def create_button(self, frame, text, command, column):
        button = ctk.CTkButton(frame, text=text, font=(
            "Helvetica", 24), width=240, height=3, command=lambda: self.run_function(command))
        button.grid(row=0, column=column, padx=20)

    def run_function(self, func):
        self.destroy()  # Close the main window
        func()  # Execute the selected functionality

    def show_info_popup(self):
        messagebox.showinfo(
            "Information", "Interfacial Tension: Measures the force at the surface of liquids.\n\nContact Angle: Measures the angle between the liquid surface and the solid surface.")
