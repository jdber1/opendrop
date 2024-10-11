from customtkinter import *
from customtkinter import CTkLabel
from tkinter import filedialog, messagebox
from PIL import ImageTk, Image
from utils.image_handler import ImageHandler
from utils.validators import validate_numeric_input

PATH_TO_SCRIPT = os.path.join(os.path.dirname(os.path.realpath(__file__)),'..')

class PdAcquisition(CTkFrame):
    def __init__(self, parent, user_input_data, **kwargs):
        super().__init__(parent, **kwargs)

        self.image_handler = ImageHandler()

        self.image_source_button = CTkButton(self, text="Filesystem", width=150, height=40)
        self.image_source_button.grid(pady=10)

        self.choose_files_button = CTkButton(self, text="Choose File(s)", command=lambda: self.select_files(), width=150, height=40)
        self.choose_files_button.grid(pady=10)

        self.images_frame = CTkFrame(self)

        self.current_index = 0

        self.user_input_data = user_input_data

        self.frame_interval_var = StringVar()
        self.frame_interval_var.trace_add("write", self.update_frame_interval)


        numberic_validate_command = self.register(validate_numeric_input)

        # Label for the input field
        self.interval_input_label = CTkLabel(self, text="Frame Intervals:")
        # Create an Entry widget with numeric validation
        self.frame_interval_entry = CTkEntry(self, textvariable=self.frame_interval_var, validate="key", validatecommand=(numberic_validate_command, '%P'))


    def select_files(self):
        # Clear previous images
        for widget in self.images_frame.winfo_children():
            widget.destroy()

        self.user_input_data.import_files = filedialog.askopenfilenames(
            title="Select Files",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp"), ("All Files", "*.*")],
            initialdir=PATH_TO_SCRIPT
        )

        # Update the button text with the number of files selected
        num_files = len(self.user_input_data.import_files)
        self.user_input_data.number_of_frames = num_files
        
        if num_files > 0:
            self.choose_files_button.configure(text=f"{num_files} File(s) Selected")

            self.images_frame.grid(padx=20, pady=20, fill="both", expand=True)

            if (num_files > 1):
                # If number of files bigger than 0, give user an opportunity to enter the frame interval
                self.interval_input_label.grid(pady=10)
                self.frame_interval_entry.grid(pady=10)

            # Image display area
            self.image_label = CTkLabel(self.images_frame, text="", fg_color="lightgrey", width=400, height=300)
            self.image_label.grid(pady=10)

            # Display the filename below the image
            file_name = os.path.basename(self.user_input_data.import_files[self.current_index])
            self.name_label = CTkLabel(self.images_frame, text=file_name, font=("Arial", 10))
            self.name_label.grid()

            # Frame to hold navigation components
            self.image_navigation_frame = CTkFrame(self.images_frame, width=50)
            self.image_navigation_frame.grid(pady=30)

            # Previous button
            self.prev_button = CTkButton(self.image_navigation_frame, text="<", command=lambda: self.change_image(-1), width=3)
            self.prev_button.grid(side="left", padx=10)

            # Initialize entry for current index
            self.index_entry = CTkEntry(self.image_navigation_frame, width=5)
            self.index_entry.grid(side="left", padx=10)
            self.index_entry.bind("<Return>", lambda event: self.update_index_from_entry())
            self.index_entry.insert(0, str(self.current_index + 1))

            # Navigation label
            self.navigation_label = CTkLabel(self.image_navigation_frame, text=f" of {num_files}", font=("Arial", 12))
            self.navigation_label.grid(side="left")

            # Next button
            self.next_button = CTkButton(self.image_navigation_frame, text=">", command=lambda: self.change_image(1), width=3)
            self.next_button.grid(side="left", padx=10)

            self.load_image(self.user_input_data.import_files[self.current_index])  # Load the first image by default
        else:
            self.images_frame.grid_forget()
            self.choose_files_button.configure(text="Choose File(s)")  # Reset if no files were chosen
            messagebox.showinfo("No Selection", "No files were selected.")

        if (num_files <= 1):
            self.interval_input_label.grid_forget()
            self.frame_interval_entry.grid_forget()

    def load_image(self, selected_image):
        """Load and display the selected image."""
        try:
            self.current_image = Image.open(selected_image)
            self.display_image()
        except FileNotFoundError:
            print(f"Error: The image file {selected_image} was not found.")
            self.current_image = None

    def display_image(self):
        """Display the currently loaded image."""
        resized_image = self.image_handler.resize_image(self.current_image)
        if resized_image:
            self.tk_image = ImageTk.PhotoImage(resized_image)
            self.image_label.configure(image=self.tk_image)
            self.image_label.image = self.tk_image  # Keep a reference to avoid garbage collection

    def change_image(self, direction):
        """Change the currently displayed image based on the direction."""
        if self.user_input_data.import_files:
            self.current_index = (self.current_index + direction) % self.user_input_data.number_of_frames
            self.load_image(self.user_input_data.import_files[self.current_index])  # Load the new image
            self.update_index_entry()  # Update the entry with the current index
            file_name = os.path.basename(self.user_input_data.import_files[self.current_index])
            self.name_label.configure(text=file_name)

    def update_index_from_entry(self):
        """Update current index based on user input in the entry."""
        try:
            new_index = int(self.index_entry.get()) - 1  # Convert to zero-based index
            if 0 <= new_index < self.user_input_data.number_of_frames:
                self.current_index = new_index
                self.load_image(self.user_input_data.import_files[self.current_index])  # Load the new image
            else:
                print("Index out of range.")
        except ValueError:
            print("Invalid input. Please enter a number.")

        self.update_index_entry()  # Update the entry display

    def update_index_entry(self):
        """Update the index entry to reflect the current index."""
        self.index_entry.delete(0, 'end')  # Clear the current entry
        self.index_entry.insert(0, str(self.current_index + 1))  # Insert the new index (1-based)

    def update_frame_interval(self, *args):
        self.user_input_data.frame_interval = self.frame_interval_var.get()
