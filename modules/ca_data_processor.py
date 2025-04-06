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
    def gather_image_data(self, user_input_data, extracted_data, i):
        print("\nProcessing frame %d of %d..." % (i+1, user_input_data.number_of_frames))
        input_file = user_input_data.import_files[i]
        print("\nProcessing " + input_file)
        time_start = timeit.default_timer()
        
        raw_experiment = ExperimentalDrop()
        get_image(raw_experiment, user_input_data, i)  # Save image
        set_drop_region(raw_experiment, user_input_data)
        extract_drop_profile(raw_experiment, user_input_data)
        
        if i == 0:
            extracted_data.initial_image_time = raw_experiment.time
        
        return raw_experiment

    def process_data(self, fitted_drop_data, user_input_data, callback):
        analysis_methods = dict(user_input_data.analysis_methods_ca)

        if analysis_methods.get(ML_MODEL):
            from modules.ML_model.prepare_experimental import prepare4model_v03, experimental_pred
            import tensorflow as tf
            tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)  # Minimize TF warnings
            model_path = './modules/ML_model/'
            model = tf.keras.models.load_model(model_path)

        n_frames = user_input_data.number_of_frames
        extracted_data = ExtractedData(n_frames, fitted_drop_data.parameter_dimensions)

        self.output = []
        
        for i in range(n_frames):
            raw_experiment = self.gather_image_data(user_input_data, extracted_data, i)
            set_surface_line(raw_experiment, user_input_data)  # Fits performed if User-selected

            # Apply fitting if baseline method is automated
            if user_input_data.baseline_method == "Automated":
                if any(analysis_methods.get(method, False) for method in [TANGENT_FIT, POLYNOMIAL_FIT, CIRCLE_FIT, ELLIPSE_FIT]):
                    perform_fits(
                        raw_experiment,
                        tangent=analysis_methods[TANGENT_FIT],
                        polynomial=analysis_methods[POLYNOMIAL_FIT],
                        circle=analysis_methods[CIRCLE_FIT],
                        ellipse=analysis_methods[ELLIPSE_FIT]
                    )

            # Apply tilt correction and ML model-based fits
            if analysis_methods.get(ML_MODEL) or analysis_methods.get(YL_FIT):
                correct_tilt(raw_experiment, user_input_data)
                extract_drop_profile(raw_experiment, user_input_data)
                if user_input_data.baseline_method == "Automated":
                    set_surface_line(raw_experiment, user_input_data)
                
                if analysis_methods.get(YL_FIT):
                    print('Performing YL fit...')
                    perform_fits(raw_experiment, YL=analysis_methods[YL_FIT])
                
                if analysis_methods.get(ML_MODEL):
                    pred_ds = prepare4model_v03(raw_experiment.drop_contour)
                    ML_predictions, timings = experimental_pred(pred_ds, model)
                    raw_experiment.contact_angles[ML_MODEL] = {
                        LEFT_ANGLE: ML_predictions[0, 0],
                        RIGHT_ANGLE: ML_predictions[1, 0],
                        'timings': timings
                    }

            extracted_data.contact_angles = raw_experiment.contact_angles
            print("Extracted outputs:")
            for key1, value1 in extracted_data.contact_angles.items():
                for key2, value2 in value1.items():
                    print(f"{key1} {key2}: {value2}")

            self.output.append(extracted_data)

            if callback:
                # make sure to pass the raw_experiment object to the callback
                callback(extracted_data, raw_experiment)

    def save_result(self, input_file, output_directory, filename):
        for index, extracted_data in enumerate(self.output):
            extracted_data.export_data(input_file, output_directory, filename, index)
