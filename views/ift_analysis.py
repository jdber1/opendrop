from customtkinter import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class IftAnalysis(CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill="both", expand=True)

        # Create and configure the CTkTabView
        self.tab_view = CTkTabview(self)  
        self.tab_view.pack(fill="both", expand=True, padx=20, pady=20)

        # Add "Results" and "Graphs" tabs
        self.tab_view.add("Results")
        self.tab_view.add("Graphs")

        # Initialize content for each tab
        self.create_table_view()
        self.create_graph_view()

    def create_table_view(self):
        results_tab = self.tab_view.tab("Results")
        label = CTkLabel(results_tab, text="Table with results goes here.")
        label.pack(padx=10, pady=10)

        # Create a frame to hold the table
        table_frame = CTkFrame(results_tab)
        table_frame.pack(padx=10, pady=10)

        # Create a grid for the table in the Results tab using pack
        for i in range(5):  # 5 rows
            row_frame = CTkFrame(table_frame)  # Create a frame for each row
            row_frame.pack(side="top", fill="x")  # Pack the row frame vertically
            for j in range(3):  # 3 columns
                cell = CTkLabel(row_frame, text=f"Cell ({i+1},{j+1})")
                cell.pack(side="left", padx=5, pady=5)  # Pack cells horizontally

    def create_graph_view(self):
        graphs_tab = self.tab_view.tab("Graphs")
        label = CTkLabel(graphs_tab, text="Graph goes here.")
        label.pack(padx=10, pady=10)

        # Create a sample graph
        fig, ax = plt.subplots(figsize=(4, 3))
        ax.plot([1, 2, 3], [1, 4, 9])  # Sample data for graph

        # Create a canvas to hold the graph in the Graphs tab
        canvas = FigureCanvasTkAgg(fig, master=graphs_tab)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        canvas.draw()