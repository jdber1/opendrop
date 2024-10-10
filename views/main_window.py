import tkinter as tk
import signal
import sys

class MainWindow(tk.Tk):
    def __init__(self, func_one, func_two):
        super().__init__()  # Initialize the Tk class
        self.title("Main Window")
        self.geometry("300x200")

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

        # Create buttons for functionality
        button_one = tk.Button(self, text="ift", command=lambda: self.run_function(func_one))
        button_one.pack(pady=20)

        button_two = tk.Button(self, text="ca", command=lambda: self.run_function(func_two))
        button_two.pack(pady=20)

        self.mainloop()  # Start the Tkinter main loop

    def run_function(self, func):
        self.destroy()  # Close the main window
        func()  # Execute the selected functionality