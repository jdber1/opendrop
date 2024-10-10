import customtkinter as ctk
from tkinter import filedialog, messagebox

class OutputPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(fg_color='white')

        # Info Button in the top-right corner (Above the tabs)
        info_button = ctk.CTkButton(self, text="❗", width=30, height=30, command=self.show_info_popup)
        info_button.place(relx=0.95, rely=0.02)

        # Tabs for navigation (Placed on a separate row)
        tab_frame = ctk.CTkFrame(self, fg_color='white')
        tab_frame.pack(fill='x', pady=(50, 10))

        tabs = ["Acquisition", "Preparation", "Analysis", "Output"]
        for tab in tabs:
            tab_btn = ctk.CTkButton(tab_frame, text=tab, corner_radius=0, font=ctk.CTkFont(size=14),
                                    fg_color="lightgray", hover_color="gray", text_color="black")
            tab_btn.pack(side='left', fill='x', expand=True)

        # Output Data Location Section
        output_frame = ctk.CTkFrame(self, fg_color='lightgray')
        output_frame.pack(fill='x', padx=20, pady=10)

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

        # Figure Section (Scrollable and Expandable)
        figure_frame = ctk.CTkFrame(self, fg_color='lightgray')
        figure_frame.pack(fill='both', padx=20, pady=20, expand=True)

        figure_label = ctk.CTkLabel(figure_frame, text="Figure", font=ctk.CTkFont(size=14, weight="bold"))
        figure_label.pack(pady=10)

        # Scrollable area for plots
        scrollable_frame = ctk.CTkScrollableFrame(figure_frame, fg_color='white', height=150)
        scrollable_frame.pack(fill='both', expand=True, padx=10, pady=5)

        self.check_vars = []
        for i in range(20):  # Example with 20 plot options to show the scalability
            var = ctk.StringVar()
            self.check_vars.append(var)
            plot_check = ctk.CTkCheckBox(scrollable_frame, text=f"Plot {i+1}", variable=var, onvalue="on", offvalue="off",
                                         command=self.update_plot_summary)
            plot_check.grid(row=i // 2, column=i % 2, padx=20, pady=5, sticky='w')

        # Plot selection summary (Centered below the plots)
        self.plot_summary_label = ctk.CTkLabel(figure_frame, text="0 plots selected", anchor='center')
        self.plot_summary_label.pack(pady=10)

        # Save and Back Buttons (Right aligned)
        button_frame = ctk.CTkFrame(self, fg_color='white')
        button_frame.pack(side='bottom', fill='x', pady=20)

        save_button = ctk.CTkButton(button_frame, text="Save", command=self.save_output)
        save_button.pack(side='right', padx=10)

        back_button = ctk.CTkButton(button_frame, text="Back", command=lambda: controller.show_previous_page())
        back_button.pack(side='right', padx=10)

        # Status Label (initially hidden)
        self.status_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=16), anchor='center')
        self.status_label.place(relx=0.5, rely=0.5, anchor='center')

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