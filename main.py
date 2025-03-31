#!/usr/bin/env python
#coding=utf-8
from __future__ import unicode_literals
from __future__ import print_function
# from modules.classes import ExperimentalDrop, DropData, Tolerances
# from modules.static_setup_class import ExperimentalSetup
# # from modules.ui import initialise_ui
# from modules.user_interface import call_user_input
# # from modules.load import load_data
# from modules.extract_data import extract_drop_profile
# from modules.initialise_parameters import initialise_parameters
# # from modules.fit_data import fit_raw_experiment
# # from modules.user_set_regions


from modules.classes import ExperimentalSetup, ExperimentalDrop, DropData, Tolerances
#from modules.PlotManager import PlotManager
from modules.ExtractData import ExtractedData

from views.main_window import MainWindow
from views.function_window import call_user_input
from modules.read_image import get_image
from modules.select_regions import set_drop_region,set_surface_line, correct_tilt
from modules.extract_profile import extract_drop_profile
from modules.extract_profile import image_crop
from modules.initialise_parameters import initialise_parameters
from utils.enums import *
#from modules.analyse_needle import calculate_needle_diameter
#from modules.fit_data import fit_experimental_drop
from modules.fits import perform_fits
#from modules.generate_data import generate_full_data
# from modules. import add_data_to_lists

import matplotlib.pyplot as plt

import os
import numpy as np
import tkinter as tk
from tkinter import font as tkFont

import timeit
import time

np.set_printoptions(suppress=True)
np.set_printoptions(precision=3)

DELTA_TOL = 1.e-6
GRADIENT_TOL = 1.e-6
MAXIMUM_FITTING_STEPS = 10
OBJECTIVE_TOL = 1.e-4
ARCLENGTH_TOL = 1.e-6
MAXIMUM_ARCLENGTH_STEPS = 10
NEEDLE_TOL = 1.e-4
NEEDLE_STEPS = 20

def main():
    clear_screen()
    
    continue_processing = {"status": True}
    
    while continue_processing["status"]:
        fitted_drop_data = DropData()
        """
        tolerances = Tolerances(
            DELTA_TOL,
            GRADIENT_TOL,
            MAXIMUM_FITTING_STEPS,
            OBJECTIVE_TOL,
            ARCLENGTH_TOL,
            MAXIMUM_ARCLENGTH_STEPS,
            NEEDLE_TOL,
            NEEDLE_STEPS)
        """
        # user_inputs = ExperimentalSetup()
        drop_info = ExperimentalDrop()
        
        MainWindow(
            continue_processing,
            lambda: call_user_input(FunctionType.PENDANT_DROP, fitted_drop_data),
            lambda: call_user_input(FunctionType.CONTACT_ANGLE, fitted_drop_data)
        )

#    cheeky_pause()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def pause_wait_time(elapsed_time, requested_time):
    if elapsed_time > requested_time:
        print('WARNING: Fitting took longer than desired wait time')
    else:
        time.sleep(requested_time - elapsed_time)

def cheeky_pause():
    import Tkinter
    import tkMessageBox
    import cv2
    #    cv2.namedWindow("Pause")
    #    while 1:
    #        k = cv2.waitKey(1) & 0xFF
    #        if (k==27):
    #            break
    #root = Tkinter.Tk()
    #    B = Tkinter.Button(top, text="Exit",command = cv2.destroyAllWindows())
    #    B = Tkinter.Button(root, text="Exit",command = root.destroy())
    #
    #    B.pack()
    #    root.mainloop()

    root = Tkinter.Tk()
    frame = Tkinter.Frame(root)
    frame.pack()

    button = Tkinter.Button(frame)
    button['text'] ="Good-bye."
    button['command'] = root.destroy()#close_window(root)
    button.pack()

    root.mainloop()

def quit_(root):
    root.quit()

#def close_window(root):
#    root.destroy()


if __name__ == '__main__':
    main()
    """
    root = tk.Tk()
    # quit button
    buttonFont = tkFont.Font(family='Helvetica', size=48, weight='bold') #This isn't working for some reason (??)
    quit_button = tk.Button(master=root, font=buttonFont,text='Quit',height=4,width=15,
                            command=lambda: quit_(root),bg='blue',fg='white',activeforeground='white',activebackground='red')
    quit_button.pack()
    
    root.mainloop()
    """
