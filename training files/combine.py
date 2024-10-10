import datetime
import os
import pickle

import numpy as np
from matplotlib import pyplot as plt
import matplotlib
matplotlib.use('Agg')
import csv

# set the initial variables
directory_path = './contour_dataset_4par/'
save_path = 'contour_dataset_4par.pkl'

# create empty dictionary
ds = {}

# define .pkl load function
def load_obj(name ):
    with open(name, 'rb') as f:
        return pickle.load(f)

# iterate over all files in the directory
for filename in os.listdir(directory_path):
    # construct the full file path
    file_path = os.path.join(directory_path, filename)

    # check if the file is a pkl file (i.e., not a directory)
    if os.path.isfile(file_path):
        # check if the file is a .pkl file
        if file_path.endswith('.pkl'):
            # load the dictionary saved in the pickle file
            data = load_obj(file_path)

            # copy each key and contour into the ds dictionary defined above
            for key in data.keys():
                ds[key] = data[key]

if save_path is not None:
    with open(save_path, 'wb') as f:
        pickle.dump(ds, f, pickle.HIGHEST_PROTOCOL)
