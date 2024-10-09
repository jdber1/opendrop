print('start of python script')

import datetime
import pickle
import numpy as np

# set the initial variables
save_path = 'contour_dataset_4par.pkl'

# make sure that the script has started correctly
print('starting...')

# define .pkl load function
def load_obj(name ):
    with open(name, 'rb') as f:
        return pickle.load(f)

ds = load_obj(save_path)

now = datetime.datetime.now()
time_str = now.strftime('%H:%M:%S')
print('dataset loaded at: ',time_str)

max_len = max([len(ds[key]) for key in ds.keys()])
min_len = min([len(ds[key]) for key in ds.keys()])

print('maximum contour length:')
print(max_len)
print('minimum contour length:')
print(min_len)

ds_new = {}

for key in ds.keys():
    a = ds[key]
    result = np.zeros((max_len,2))
    result[:a.shape[0],:a.shape[1]] = a
    ds_new[key] = result

now = datetime.datetime.now()
time_str = now.strftime('%H:%M:%S')
print('zero-padded dataset created at: ',time_str)

max_len_new = max([len(ds_new[key]) for key in ds_new.keys()])
min_len_new = min([len(ds_new[key]) for key in ds_new.keys()])

print('maximum contour length:')
print(max_len_new)
print('minimum contour length:')
print(min_len_new)

with open(save_path, 'wb') as f:
    pickle.dump(ds_new, f, pickle.HIGHEST_PROTOCOL)

print('saved')
print('done')
