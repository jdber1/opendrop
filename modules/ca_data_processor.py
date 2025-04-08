from modules.classes import ExperimentalSetup, ExperimentalDrop, DropData, Tolerances
#from modules.PlotManager import PlotManager
from modules.ExtractData import ExtractedData
from modules.read_image import get_image
from modules.select_regions import set_drop_region,set_surface_line, correct_tilt
from modules.extract_profile import extract_drop_profile
from utils.enums import *
from utils.config import *
from modules.fits import perform_fits

import matplotlib.pyplot as plt

import os
import numpy as np
import tkinter as tk
from tkinter import font as tkFont

import timeit

class CaDataProcessor:
    def process_data(self, fitted_drop_data, user_input_data, callback):

        analysis_methods = dict(user_input_data.analysis_methods_ca)

        if analysis_methods[ML_MODEL]:
            from modules.ML_model.prepare_experimental import prepare4model_v03, experimental_pred
            import tensorflow as tf
            tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR) # to minimise tf warnings
            model_path = './modules/ML_model/'
            model = tf.keras.models.load_model(model_path)

        n_frames = user_input_data.number_of_frames
        extracted_data = ExtractedData(n_frames, fitted_drop_data.parameter_dimensions)
        raw_experiment = ExperimentalDrop()

        #if user_input_data.interfacial_tension_boole:
        #    plots = PlotManager(user_input_data.wait_time, n_frames)

        #get_image(raw_experiment, user_input_data, -1) #is this needed?

        self.output = []

        for i in range(n_frames):
            print("\nProcessing frame %d of %d..." % (i+1, n_frames))
            input_file = user_input_data.import_files[i]
            print("\nProceccing " + input_file)
            time_start = timeit.default_timer()
            raw_experiment = ExperimentalDrop()
            get_image(raw_experiment, user_input_data, i) # save image in here...
            set_drop_region(raw_experiment, user_input_data)
            # extract_drop_profile(raw_experiment, user_input_data)
            extract_drop_profile(raw_experiment, user_input_data)

            if i == 0:
                extracted_data.initial_image_time = raw_experiment.time

            set_surface_line(raw_experiment, user_input_data) #fits performed here if baseline_method is User-selected

            # these methods don't need tilt correction
            if user_input_data.baseline_method == "Automated":
                if analysis_methods[TANGENT_FIT] or analysis_methods[POLYNOMIAL_FIT] or analysis_methods[CIRCLE_FIT] or analysis_methods[ELLIPSE_FIT]:
                    perform_fits(raw_experiment, tangent=analysis_methods[TANGENT_FIT], 
                                 polynomial=analysis_methods[POLYNOMIAL_FIT], circle=analysis_methods[CIRCLE_FIT],
                                 ellipse=analysis_methods[ELLIPSE_FIT])

            # YL fit and ML model need tilt correction
            if analysis_methods[ML_MODEL] or analysis_methods[YL_FIT]:
                correct_tilt(raw_experiment, user_input_data)
                extract_drop_profile(raw_experiment, user_input_data)
                if user_input_data.baseline_method == "Automated":
                    set_surface_line(raw_experiment, user_input_data)
                # experimental_setup.baseline_method == 'User-selected' should work as is

                #raw_experiment.contour = extract_edges_CV(raw_experiment.cropped_image, threshold_val=raw_experiment.ret, return_thresholed_value=False)
                #experimental_drop.drop_contour, experimental_drop.contact_points = prepare_hydrophobic(experimental_drop.contour)

                if analysis_methods[YL_FIT]:
                    print('Performing YL fit...')
                    perform_fits(raw_experiment, YL=analysis_methods[YL_FIT])
                if analysis_methods[ML_MODEL]:
                    pred_ds = prepare4model_v03(raw_experiment.drop_contour)
                    ML_predictions, timings = experimental_pred(pred_ds, model)
                    raw_experiment.contact_angles[ML_MODEL] = {}
                    # raw_experiment.contact_angles[ML_MODEL]['angles'] = [ML_predictions[0,0],ML_predictions[1,0]]
                    raw_experiment.contact_angles[ML_MODEL][LEFT_ANGLE] = ML_predictions[0,0]
                    raw_experiment.contact_angles[ML_MODEL][RIGHT_ANGLE] = ML_predictions[1,0]
                    raw_experiment.contact_angles[ML_MODEL]['timings'] = timings

            extracted_data.contact_angles = raw_experiment.contact_angles # DS 7/6/21

            #print(extracted_data.contact_angles) #for the dictionary output
            print('Extracted outputs:')
            for key1 in extracted_data.contact_angles.keys():
                for key2 in extracted_data.contact_angles[key1].keys():
                    print(key1+' '+key2+': ')
                    print('    ',extracted_data.contact_angles[key1][key2])
                    print()

            self.output.append(extracted_data)

            if callback:
                callback(extracted_data,raw_experiment)

    def save_result(self, input_file, output_directory, filename):
        for index, extracted_data in enumerate(self.output):
            extracted_data.export_data(input_file, output_directory, filename, index)