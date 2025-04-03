from customtkinter import CTk
# Import the MainWindow class from main_window.py
from ui.main_window import MainWindow


def main():
    # Create the main application window
    app = MainWindow()
    # Run the application
    app.mainloop()


if __name__ == "__main__":
    main()
