import tkinter as tk
import sys
import signal
from tkinter import messagebox

from views.contact_angle_window import ContactAngleWindow
from views.pendant_drop_window import PenDantDropWindow


class MainWindow(tk.Tk):
    def __init__(self, func_one, func_two):
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

        # Set up close and minimize buttons
        close_button = tk.Button(self, text="X", command=self.close_window, bg="white", fg="black", bd=0, font=("Arial", 12, "bold"))
        close_button.place(x=760, y=5)

        minimize_button = tk.Button(self, text="—", command=self.minimize_window, bg="white", fg="black", bd=0, font=("Arial", 12, "bold"))
        minimize_button.place(x=720, y=5)

        # Display title
        title_label = tk.Label(self, text="OpenDrop2", font=("Helvetica", 48))
        title_label.pack(pady=50)

        # Create main functionality buttons
        button_frame = tk.Frame(self)
        button_frame.pack(pady=50)

        # Bind the buttons to the same functions as in the old code
        self.create_button(button_frame, "Interfacial Tension", func_one, 0)
        self.create_button(button_frame, "Contact Angle", func_two, 1)

        # Add information button at bottom-right corner
        info_button = tk.Button(self, text="❗", command=self.show_info_popup, bg="white", fg="black", bd=0, font=("Arial", 12, "bold"))
        info_button.place(relx=1.0, rely=1.0, anchor='se', x=-10, y=-10)  # Positioned in the bottom-right corner

    def create_button(self, frame, text, command, column):
        button = tk.Button(frame, text=text, font=("Helvetica", 24), width=15, height=3, command=command)
        button.grid(row=0, column=column, padx=20)

    def close_window(self):
        self.destroy()

    def minimize_window(self):
        self.iconify()

    def show_info_popup(self):
        messagebox.showinfo("Information", "Interfacial Tension: Measures the force at the surface of liquids.\n\nContact Angle: Measures the angle between the liquid surface and the solid surface.")

# Assuming `func_one` is the function related to the "ift" functionality from the old code
# and `func_two` is the function related to the "ca" functionality
def run_interfacial_tension(self):
    self.destroy()  # Close the current window
    user_input_data = None  # If any user input data is required
    PenDantDropWindow(user_input_data)  # Open the PenDantDropWindow
    print("Running Interfacial Tension")

def run_contact_angle(self):
    # Close MainWindow and switch to ContactAngleWindow
    self.destroy()
    ContactAngleWindow(user_input_data={})  # Assuming user_input_data is passed to the next window
    print("Running Contact Angle")

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
