import customtkinter as ctk
from tkinter import filedialog, messagebox


class OutputPage(ctk.CTkFrame):
    def __init__(self, parent, user_input_data, controller):
        super().__init__(parent)
        self.controller = controller

        # Set up the grid configuration for the entire frame
        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Output Data Location Section
        output_frame = ctk.CTkFrame(self)
        output_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        # Output Location Label inside the gray frame (output_frame)
        output_location_label = ctk.CTkLabel(
            output_frame, text="Output Location", font=ctk.CTkFont(size=14, weight="bold"), anchor="w")
        output_location_label.grid(
            row=0, column=0, columnspan=3, padx=10, pady=(10, 5), sticky="w")

        location_label = ctk.CTkLabel(
            output_frame, text="Location:", anchor='w')
        location_label.grid(row=1, column=0, sticky='w', padx=10, pady=5)
        self.location_entry = ctk.CTkEntry(output_frame, width=300)
        self.location_entry.grid(row=1, column=1, padx=10, pady=5)
        browse_btn = ctk.CTkButton(
            output_frame, text="Browse", command=self.browse_location)
        browse_btn.grid(row=1, column=2, padx=10, pady=5)

        filename_label = ctk.CTkLabel(
            output_frame, text="Filename:", anchor='w')
        filename_label.grid(row=2, column=0, sticky='w', padx=10, pady=5)
        self.filename_entry = ctk.CTkEntry(output_frame, width=300)
        self.filename_entry.grid(row=2, column=1, padx=10, pady=5)

        # Figure Section
        figure_frame = ctk.CTkFrame(self)
        figure_frame.grid(row=2, column=0, padx=20, pady=20, sticky="nsew")

        figure_label = ctk.CTkLabel(
            figure_frame, text="Figure", font=ctk.CTkFont(size=14, weight="bold"))
        figure_label.pack(pady=10)

        # Scrollable area for plots
        scrollable_frame = ctk.CTkScrollableFrame(
            figure_frame, height=150)
        scrollable_frame.pack(fill='both', expand=True, padx=10, pady=5)

        self.check_vars = []
        for i in range(20):
            var = ctk.StringVar()
            self.check_vars.append(var)
            plot_check = ctk.CTkCheckBox(scrollable_frame, text=f"Plot {i+1}", variable=var, onvalue="on", offvalue="off",
                                         command=self.update_plot_summary)
            plot_check.grid(row=i // 2, column=i %
                            2, padx=20, pady=5, sticky='w')

        # Plot selection summary (Centered below the plots)
        self.plot_summary_label = ctk.CTkLabel(
            figure_frame, text="0 plots selected", anchor='center')
        self.plot_summary_label.pack(pady=10)

    def browse_location(self):
        directory = filedialog.askdirectory()
        if directory:
            self.location_entry.insert(0, directory)

    def save_output(self):
        location = self.location_entry.get()
        filename = self.filename_entry.get()
        if not location or not filename:
            messagebox.showerror(
                "Error", "Please specify a location and filename.")
            return

        # Simulate a delay to mimic saving process (3 seconds here)
        self.after(3000, self.show_saved_status)

    def show_saved_status(self):
        # Update the status to "Saved!" and keep the style
        messagebox.showinfo("Success", "File saved successfully!")

    def update_plot_summary(self):
        selected_count = sum(var.get() == "on" for var in self.check_vars)
        self.plot_summary_label.configure(
            text=f"{selected_count} plots selected")
