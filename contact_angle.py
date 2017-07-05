#!/usr/bin/env python
# coding=utf-8
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
from modules.PlotManager import PlotManager
from modules.contact_extract_data import ContactExtractedData

from modules.conAn_user_interface import call_user_input
from modules.read_image import get_image
from modules.conAn_select_regions import set_drop_region, set_surface_line
from modules.contact_extract_profile import ContactExtractProfile
from modules.contactNeedle_extract_profile import ContactNeedleExtractProfile


# from modules. import add_data_to_lists

import matplotlib.pyplot as plt

import os
import numpy as np
import Tkinter as tk
import tkFont

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


def contactAngle(conAn_type,auto_test):
    #clear_screen()
    fitted_drop_data = DropData()
    tolerances = Tolerances(
        DELTA_TOL,
        GRADIENT_TOL,
        MAXIMUM_FITTING_STEPS,
        OBJECTIVE_TOL,
        ARCLENGTH_TOL,
        MAXIMUM_ARCLENGTH_STEPS,
        NEEDLE_TOL,
        NEEDLE_STEPS)

    user_inputs = ExperimentalSetup()
    user_inputs.conAn_type = conAn_type
    if auto_test != None:
        user_inputs.auto_test_parameters = auto_test

    call_user_input(user_inputs)
    n_frames = user_inputs.number_of_frames

    if conAn_type == 1:
        extract_profile = ContactExtractProfile()

    if conAn_type == 2 :
        extract_profile = ContactNeedleExtractProfile()


    extracted_data = ContactExtractedData(n_frames, fitted_drop_data.parameter_dimensions)
    raw_experiment = ExperimentalDrop()

    if user_inputs.interfacial_tension_boole:
        plots = PlotManager(user_inputs.wait_time, n_frames)

    get_image(raw_experiment, user_inputs, -1)

    for i in range(n_frames):
        print("\nProcessing frame %d of %d..." % (i + 1, n_frames))
        time_start = timeit.default_timer()
        #raw_experiment = ExperimentalDrop()
        get_image(raw_experiment, user_inputs, i)  # save image in here...
        set_drop_region(raw_experiment, user_inputs)

        # extract_drop_profile(raw_experiment, user_inputs)
        extract_profile.extract_drop_profile(raw_experiment, user_inputs)

        #         croppedImage = image_crop(raw_experiment.image, user_inputs.drop_region)
        #         xx = np.array([0,croppedImage.shape[1]])

        #         plt.imshow(croppedImage, origin='upper', cmap = 'gray')
        # #        plt.plot(contour_x,contour_y,"--",color="white",linewidth = 2.0)
        #         plt.plot(raw_experiment.drop_data[:,0],-raw_experiment.drop_data[:,1],color="white",linewidth=2.0)
        #         plt.plot(xx,raw_experiment.surface_data(xx),'r--',linewidth=2.0)

        #         plt.show()

        # plt.hold()
        if i == 0:
            extracted_data.initial_image_time = raw_experiment.time
            filename = user_inputs.filename[:-4] + '_' + user_inputs.time_string + ".csv"
            export_filename = os.path.join(user_inputs.directory_string, filename)

        set_surface_line(raw_experiment, user_inputs)

        extracted_data.contact_angles[i, 0] = raw_experiment.contact_angles[0]
        extracted_data.contact_angles[i, 1] = raw_experiment.contact_angles[1]

        if conAn_type == 1 and auto_test != None:
            file_object = open(os.path.dirname(__file__) + '/standard_outputs/contactAn.txt', 'r')
            string = file_object.readline()
            file_object.close()

            if string == str(raw_experiment.contact_angles[0]) + "," + str(raw_experiment.contact_angles[1]):
                print("contact angle are correct")
            else:
                print("contact angle are incorrect")

        if conAn_type == 2 and auto_test != None:
            file_object = open(os.path.dirname(__file__) + '/standard_outputs/contactAnNeedle.txt', 'r')
            string = file_object.readline()
            file_object.close()

            if string == str(raw_experiment.contact_angles[0]) + "," + str(raw_experiment.contact_angles[1]):
                print("contact angle are correct")
            else:
                print("contact angle are incorrect")

        print(extracted_data.contact_angles[i, :])

        # fit_experimental_drop(raw_experiment, fitted_drop_data, user_inputs, tolerances)
        # generate_full_data(extracted_data, raw_experiment, fitted_drop_data, user_inputs, i)
        # data_vector = extracted_data.time_IFT_vol_area(i)
        # if user_inputs.interfacial_tension_boole:
        #     plots.append_data_plot(data_vector, i)
        # if i != (n_frames - 1):
        #     time_loop = timeit.default_timer() - time_start
        #     pause_wait_time(time_loop, user_inputs.wait_time)
        extracted_data.export_data(export_filename, i)
    if (auto_test != None):
        os._exit(0)

    root = tk.Tk()
    # quit button
    buttonFont = tkFont.Font(family='Helvetica', size=48, weight='bold')  # This isn't working for some reason (??)
    quit_button = tk.Button(master=root, font=buttonFont, text='Quit', height=4, width=15,
                            command=lambda: quit_(root), bg='blue', fg='white', activeforeground='white',
                            activebackground='red')
    quit_button.pack()
    root.mainloop()


# cheeky_pause()

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
    # root = Tkinter.Tk()
    #    B = Tkinter.Button(top, text="Exit",command = cv2.destroyAllWindows())
    #    B = Tkinter.Button(root, text="Exit",command = root.destroy())
    #
    #    B.pack()
    #    root.mainloop()

    root = Tkinter.Tk()
    frame = Tkinter.Frame(root)
    frame.pack()

    button = Tkinter.Button(frame)
    button['text'] = "Good-bye."
    button['command'] = root.destroy()  # close_window(root)
    button.pack()

    root.mainloop()


def quit_(root):
    root.destroy()


# def close_window(root):
#    root.destroy()

