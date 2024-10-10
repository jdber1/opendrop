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

from views.contact_angle_window import call_user_input as ca_call_user_input
from views.pendant_drop_window import call_user_input as pd_call_user_input
from views.main_window import MainWindow
from modules.read_image import get_image
from modules.select_regions import set_drop_region,set_surface_line, correct_tilt
from modules.extract_profile import extract_drop_profile
from modules.extract_profile import image_crop
from modules.initialise_parameters import initialise_parameters
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

def contact_angle(fitted_drop_data, user_inputs):

    # open the contact angle window
    ca_call_user_input(user_inputs)

    if user_inputs.ML_boole == True:
        from modules.ML_model.prepare_experimental import prepare4model_v03, experimental_pred
        import tensorflow as tf
        tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR) # to minimise tf warnings
        model_path = './modules/ML_model/'
        model = tf.keras.models.load_model(model_path)

    n_frames = user_inputs.number_of_frames
    extracted_data = ExtractedData(n_frames, fitted_drop_data.parameter_dimensions)
    raw_experiment = ExperimentalDrop()

    #if user_inputs.interfacial_tension_boole:
    #    plots = PlotManager(user_inputs.wait_time, n_frames)

    #get_image(raw_experiment, user_inputs, -1) #is this needed?

    for i in range(n_frames):
        print("\nProcessing frame %d of %d..." % (i+1, n_frames))
        input_file = user_inputs.import_files[i]
        print("\nProceccing " + input_file)
        time_start = timeit.default_timer()
        raw_experiment = ExperimentalDrop()
        get_image(raw_experiment, user_inputs, i) # save image in here...
        set_drop_region(raw_experiment, user_inputs)
        # extract_drop_profile(raw_experiment, user_inputs)
        extract_drop_profile(raw_experiment, user_inputs)


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

        set_surface_line(raw_experiment, user_inputs) #fits performed here if baseline_method is User-selected

        # these methods don't need tilt correction
        if user_inputs.baseline_method == "Automated":
            if user_inputs.tangent_boole == True or user_inputs.second_deg_polynomial_boole == True or user_inputs.circle_boole == True or user_inputs.ellipse_boole == True:
                perform_fits(raw_experiment, tangent=user_inputs.tangent_boole, polynomial=user_inputs.second_deg_polynomial_boole, circle=user_inputs.circle_boole,ellipse=user_inputs.ellipse_boole)

        # YL fit and ML model need tilt correction
        if user_inputs.ML_boole == True or user_inputs.YL_boole == True:
            correct_tilt(raw_experiment, user_inputs)
            extract_drop_profile(raw_experiment, user_inputs)
            if user_inputs.baseline_method == "Automated":
                set_surface_line(raw_experiment, user_inputs)
            # experimental_setup.baseline_method == 'User-selected' should work as is

            #raw_experiment.contour = extract_edges_CV(raw_experiment.cropped_image, threshold_val=raw_experiment.ret, return_thresholed_value=False)
            #experimental_drop.drop_contour, experimental_drop.contact_points = prepare_hydrophobic(experimental_drop.contour)

            if user_inputs.YL_boole == True:
                print('Performing YL fit...')
                perform_fits(raw_experiment, YL=user_inputs.YL_boole)
            if user_inputs.ML_boole == True:
                pred_ds = prepare4model_v03(raw_experiment.drop_contour)
                ML_predictions, timings = experimental_pred(pred_ds, model)
                raw_experiment.contact_angles['ML model'] = {}
                raw_experiment.contact_angles['ML model']['angles'] = [ML_predictions[0,0],ML_predictions[1,0]]
                raw_experiment.contact_angles['ML model']['timings'] = timings

        extracted_data.contact_angles = raw_experiment.contact_angles # DS 7/6/21

        #print(extracted_data.contact_angles) #for the dictionary output
        print('Extracted outputs:')
        for key1 in extracted_data.contact_angles.keys():
            for key2 in extracted_data.contact_angles[key1].keys():
                print(key1+' '+key2+': ')
                print('    ',extracted_data.contact_angles[key1][key2])
                print()

        # LMF least-squares fit (was commented out before)
        #fit_experimental_drop(raw_experiment, fitted_drop_data, user_inputs, tolerances)
        #generate_full_data(extracted_data, raw_experiment, fitted_drop_data, user_inputs, i)
        #data_vector = extracted_data.time_IFT_vol_area(i)
        #if user_inputs.interfacial_tension_boole:
        #    plots.append_data_plot(data_vector, i)
        #if i != (n_frames - 1):
        #    time_loop = timeit.default_timer() - time_start
        #    pause_wait_time(time_loop, user_inputs.wait_time)


        extracted_data.export_data(input_file,filename,i)

def pendant_drop(fitted_drop_data, user_inputs):
    pd_call_user_input(user_inputs)

    # TO DO: implement tenpendant drop tensiometry analysis


def main():
    clear_screen()
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

    app = MainWindow(
        lambda: pendant_drop(fitted_drop_data, user_inputs),
        lambda: contact_angle(fitted_drop_data, user_inputs)
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
    root = tk.Tk()
    # quit button
    buttonFont = tkFont.Font(family='Helvetica', size=48, weight='bold') #This isn't working for some reason (??)
    quit_button = tk.Button(master=root, font=buttonFont,text='Quit',height=4,width=15,
                            command=lambda: quit_(root),bg='blue',fg='white',activeforeground='white',activebackground='red')
    quit_button.pack()
    root.mainloop()
