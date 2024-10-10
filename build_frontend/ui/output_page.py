import customtkinter as ctk
from tkinter import filedialog, messagebox

class OutputPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(fg_color='white')

        # Set up the grid configuration for the entire frame
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Navigation frame
        navigation_frame = self.create_navigation(self)
        navigation_frame.grid(row=0, column=0, pady=(20, 10), sticky="ew")

        # Info Button in the top-right corner (Above the tabs)
        info_button = ctk.CTkButton(self, text="❗", width=30, height=30, command=self.show_info_popup)
        info_button.grid(row=0, column=0, sticky='ne', padx=(0, 10), pady=(10, 0))

        # Output Data Location Section
        output_frame = ctk.CTkFrame(self, fg_color='lightgray')
        output_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        location_label = ctk.CTkLabel(output_frame, text="Location:", anchor='w')
        location_label.grid(row=0, column=0, sticky='w', padx=10, pady=5)
        self.location_entry = ctk.CTkEntry(output_frame, width=300)
        self.location_entry.grid(row=0, column=1, padx=10, pady=5)
        browse_btn = ctk.CTkButton(output_frame, text="Browse", command=self.browse_location)
        browse_btn.grid(row=0, column=2, padx=10, pady=5)

        filename_label = ctk.CTkLabel(output_frame, text="Filename:", anchor='w')
        filename_label.grid(row=1, column=0, sticky='w', padx=10, pady=5)
        self.filename_entry = ctk.CTkEntry(output_frame, width=300)
        self.filename_entry.grid(row=1, column=1, padx=10, pady=5)

        # Figure Section
        figure_frame = ctk.CTkFrame(self, fg_color='lightgray')
        figure_frame.grid(row=2, column=0, padx=20, pady=20, sticky="nsew")

        figure_label = ctk.CTkLabel(figure_frame, text="Figure", font=ctk.CTkFont(size=14, weight="bold"))
        figure_label.pack(pady=10)

        # Scrollable area for plots
        scrollable_frame = ctk.CTkScrollableFrame(figure_frame, fg_color='white', height=150)
        scrollable_frame.pack(fill='both', expand=True, padx=10, pady=5)

        self.check_vars = []
        for i in range(20):
            var = ctk.StringVar()
            self.check_vars.append(var)
            plot_check = ctk.CTkCheckBox(scrollable_frame, text=f"Plot {i+1}", variable=var, onvalue="on", offvalue="off",
                                         command=self.update_plot_summary)
            plot_check.grid(row=i // 2, column=i % 2, padx=20, pady=5, sticky='w')

        # Plot selection summary (Centered below the plots)
        self.plot_summary_label = ctk.CTkLabel(figure_frame, text="0 plots selected", anchor='center')
        self.plot_summary_label.pack(pady=10)

        # Save and Back Buttons (Right aligned using grid)
        button_frame = ctk.CTkFrame(self, fg_color='white')
        button_frame.grid(row=3, column=0, pady=20, padx=20, sticky="se")

        button_frame.grid_columnconfigure((0, 1), weight=1)

        back_button = ctk.CTkButton(button_frame, text="Back", command=lambda: controller.show_previous_page())
        back_button.grid(row=0, column=0, sticky='e', padx=10)

        save_button = ctk.CTkButton(button_frame, text="Save", command=self.save_output)
        save_button.grid(row=0, column=1, sticky='e', padx=10)

    def create_navigation(self, parent):
        # Create a frame for the navigation
        navigation_frame = ctk.CTkFrame(parent, fg_color="lightgray")
        
        # Define stage labels for navigation
        stages = ["Acquisition", "Preparation", "Analysis", "Output"]
        
        # Create a label for each stage
        for index, stage in enumerate(stages):
            stage_label = ctk.CTkLabel(navigation_frame, text=stage, text_color="black")
            stage_label.grid(row=0, column=index, padx=20, pady=10, sticky="nsew")
            
            # Create a dot to indicate the current stage
            dot = ctk.CTkCanvas(navigation_frame, width=10, height=10, bg="white", highlightthickness=0)
            dot.grid(row=1, column=index, padx=10)
            dot.create_oval(2, 2, 8, 8, fill="black")  # Draw the dot
            
            # Make stage label responsive
            navigation_frame.grid_columnconfigure(index, weight=1)

        return navigation_frame

    def browse_location(self):
        directory = filedialog.askdirectory()
        if directory:
            self.location_entry.insert(0, directory)

    def save_output(self):
        location = self.location_entry.get()
        filename = self.filename_entry.get()
        if not location or not filename:
            messagebox.showerror("Error", "Please specify a location and filename.")
            return
        
        # Show "Saving..." message
        self.status_label.configure(text="Saving...", fg_color="lightgray")
        self.status_label.update()

        # Simulate a delay to mimic saving process (3 seconds here)
        self.after(3000, self.show_saved_status)

    def show_saved_status(self):
        # Update the status to "Saved!" and keep the style
        self.status_label.configure(text="Saved!", fg_color="lightgray")
        self.status_label.update()

    def update_plot_summary(self):
        selected_count = sum(var.get() == "on" for var in self.check_vars)
        self.plot_summary_label.configure(text=f"{selected_count} plots selected")

    def show_info_popup(self):
        messagebox.showinfo("Information", "This is a brief guide about how to use the Output section. Make sure to fill in all required fields.")

class MainApplication(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("OpenDrop-ML")
        self.geometry("800x600")
        container = ctk.CTkFrame(self)
        container.pack(fill="both", expand=True)

        self.frames = {}
        output_page = OutputPage(parent=container, controller=self)
        output_page.pack(fill="both", expand=True)
        self.frames["OutputPage"] = output_page

    def show_previous_page(self):
        pass

if __name__ == "__main__":
    ctk.set_appearance_mode("light")  # Options: "light", "dark", "system"
    ctk.set_default_color_theme("blue")  # Options: "blue", "green", "dark-blue"
    app = MainApplication()
    app.mainloop()
