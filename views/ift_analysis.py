from customtkinter import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class IftAnalysis(CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)

        self.content_frame = None
   
        # Initialize the button frame at the top
        self.toggle_results()
        
        # Below it should be the table or the graph
        self.table()     

    def toggle_results(self):
        # Create a frame to hold buttons, placing it at the top center
        button_frame = CTkFrame(self)
        button_frame.pack(side="top", pady=10)  # Placing it at the top with vertical padding
        
        # Create buttons inside the button frame
        self.results_button = CTkButton(button_frame, text="Results", command=self.table)
        self.results_button.grid(row=0, column=0, padx=5)

        # Initially disabled
        self.results_button.configure(state="disabled")

        self.graphs_button = CTkButton(button_frame, text="Graphs", command=self.graph)
        self.graphs_button.grid(row=0, column=1, padx=5)
        
        # To center the buttons in the frame
        button_frame.pack(anchor="n", pady=10)  # "n" is for top-center alignment

    def graph(self):
        self.graphs_button.configure(state="disabled")
        self.results_button.configure(state="normal")
        self.clear_content_frame()
        
        fig, ax = plt.subplots(figsize=(4, 3))
        ax.plot([1, 2, 3], [1, 4, 9])  # Sample data for graph

        canvas = FigureCanvasTkAgg(fig, master=self.content_frame)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        canvas.draw()

    def table(self):
        self.results_button.configure(state="disabled")
        self.graphs_button.configure(state="normal")
        self.clear_content_frame()

        for i in range(5):  # 5 rows
            for j in range(3):  # 3 columns
                cell = CTkLabel(self.content_frame, text=f"Cell ({i+1},{j+1})")
                cell.grid(row=i, column=j, padx=10, pady=10)

    def clear_content_frame(self):
        if self.content_frame:
            self.content_frame.destroy()

        # Create a new content frame
        self.content_frame = CTkFrame(self)
        self.content_frame.pack(fill="both", expand=True)