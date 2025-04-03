# repeat the above but on a fraction of the contour models data


import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import pickle5 as pickle
import random
import numpy as np
import datetime
import time
import os

import tensorflow as tf
from tensorflow.keras import layers
from tensorflow.keras.models import Sequential
from tensorflow.keras.callbacks import Callback # for early stopping
from tensorflow.keras.callbacks import ModelCheckpoint #for checkpoint saves
import warnings # for early stopping

import logging #for optuna logging
import sys #for optuna logging

import optuna #for hyperparameter optimisation
from optuna.integration import TFKerasPruningCallback
from optuna.trial import TrialState

# define .pkl load function
def load_obj(name ):
    with open(name, 'rb') as f:
        return pickle.load(f)

def load_dataset():
    data = load_obj('contour_dataset_4par.pkl')
    #data2 = load_obj('/data/gpfs/projects/punim1991/dgshaw/model_v03/test11/test11.2/contour_dataset_4par_ref3_-0.2to-0.08.pkl')
    #data2 = load_obj('/data/gpfs/projects/punim1991/dgshaw/model_v03/contour_dataset_4par_ref3_1223.pkl')
    #data = {**data1, **data2}
    labels = list(data.keys())
    random.Random(666).shuffle(labels)

    # train on 20% of the data to try train faster, then retrain on the whole dataset once hyperparameters are optimised
    twentypercent = int(len(labels)*0.2)
    eightypercent = int(twentypercent*0.8)
    train_keys = labels[:eightypercent]
    test_keys = labels[eightypercent:twentypercent]

    # turn data into arrays
    def create_data_arr(keys,data):
        data_set = []
        for n in keys:
            data_set.append(data[n])
        return np.array(data_set)

    train_ds = create_data_arr(train_keys,data)
    test_ds = create_data_arr(test_keys,data)

    # make sure everything is arrays, ds's are created as arrays above
    train_keys = np.array([eval(key.split('_')[0]) for key in train_keys])
    test_keys = np.array([eval(key.split('_')[0]) for key in test_keys])

    return train_ds, train_keys, test_ds, test_keys


class EarlyStoppingWhenErrorLow(Callback):
    def __init__(self, monitor='val_mse', value=0.02, verbose=0):
        super(Callback, self).__init__()
        self.monitor = monitor
        self.value = value
        self.verbose = verbose

    def on_epoch_end(self, epoch, logs={}):
        current = logs.get(self.monitor)
        if current is None:
            warnings.warn("Early stopping requires %s available!" % self.monitor, RuntimeWarning)

        elif current < self.value:
            if self.verbose > 0:
                print("Epoch %05d: early stopping THR" % epoch)
            self.model.stop_training = True

def CA_activation(x):
    return tf.keras.activations.relu(x,max_value=180)

def create_model(trial):

    # Hyperparameters to be tuned by Optuna.
    learning_rate = 0.00011638101163629009 #trial.suggest_float("learning_rate", 1e-4, 1e-1, log=True)
    batch_size = 42 #trial.suggest_int("batch_size", 32, 128, log=True)
    model_width = 32 #trial.suggest_categorical("model_width", [8,16, 32, 64, 128, 256, 512, 1024])
    es_patience = 512 #trial.suggest_int("es_patience", 1024, 1025, log=True)

    # Compose neural network with one hidden layer.
    model = Sequential([
        layers.Conv1D(model_width, 3, padding='same', activation='relu'),
        layers.Conv1D(model_width/2, 3, padding='same', activation='relu'),
        layers.Conv1D(model_width/4, 3, padding='same', activation='relu'),
        layers.Flatten(),
        layers.Dense(128, activation=CA_activation),
        layers.Dense(1)
    ])

    # Compile model.
    model.compile(
        optimizer=tf.keras.optimizers.Adam(
            learning_rate=learning_rate),
        loss="mean_squared_error",
        #metrics=(['mean_absolute_error'],['mean_squared_error'])
        metrics=(['mean_absolute_error', 'mean_squared_error'])
    )

    return model, es_patience

def load_model(trial):
    model_path = '/data/gpfs/projects/punim1991/dgshaw/model_v03/test11/test11.3/_mse_0.4399887025356293'
    learning_rate = 0.00011638101163629009 #trial.suggest_float("learning_rate", 1e-4, 1e-1, log=True)
    es_patience = 512 #1024 #trial.suggest_int("es_patience", 1024, 1025, log=True)

    model = tf.keras.models.load_model(model_path)

    model.load_weights("./weights.best.hdf5")

    model.compile(
        optimizer=tf.keras.optimizers.Adam(
            learning_rate=learning_rate),
        loss="mean_squared_error",
        metrics=(['mean_absolute_error'],['mean_squared_error'])
    )

    return model, es_patience

def objective(trial):

    # Clear clutter from previous TensorFlow graphs.
    tf.keras.backend.clear_session()

    # prep for info collection
    model_start_time = time.time()
    write = []
    write.append('TRAINING DATA\n')

    # Metrics to be monitored by Optuna.
    monitor = "val_mean_squared_error"

    # Register the custom activation function in the custom_objects dictionary
    custom_objects = {"CA_activation": CA_activation}

    # Create tf.keras model instance.
    model, es_patience = create_model(trial) # no model to load, create new model
    #model, es_patience = load_model(trial) # load model from saved model file
    #model = tf.keras.models.load_model("weights.best.hdf5", custom_objects=custom_objects) # load model from saved weights
    #es_patience = 512 # es_patience must be defined here if loading model from saved weights

    # Create dataset instance.
    train_ds, train_keys, test_ds, test_keys = load_dataset()
    print('dataset loaded...')

    baseline = 0.02
    max_epochs = #100*es_patience
    checkpointpath = "weights.best.hdf5"
    checkpoint = ModelCheckpoint(checkpointpath, monitor=monitor, verbose=0, save_best_only=True, mode='min')
    es = tf.keras.callbacks.EarlyStopping(monitor=monitor, patience=es_patience, verbose=0, mode="min", restore_best_weights=True)
    floor= EarlyStoppingWhenErrorLow(monitor=monitor, value=baseline, verbose=0)

    history = model.fit(
        train_ds, train_keys,
        validation_split=0.25,
        epochs=max_epochs,
        callbacks=[checkpoint,floor,es]#,TFKerasPruningCallback(trial, monitor)]
    )

    # record info
    training_time = time.time() - model_start_time
    write.append("--- %s seconds ---" % training_time)
    mae = history.history['mean_absolute_error']
    val_mae = history.history['val_mean_absolute_error']
    mse = history.history['mean_squared_error']
    val_mse = history.history['val_mean_squared_error']
    loss = history.history['loss']
    val_loss = history.history['val_loss']

    score = history.history[monitor][-1]
    score_dir = '_mse_'+str(score)
    model.save(str(score_dir))

    with open(str(score_dir)+'/trainHistoryDict.pkl', 'wb') as f:
        pickle.dump(history.history, f)
    # to load: history = pickle.load(open('/trainHistoryDict'), "rb")

    with open(str(score_dir)+'/modelsummary.txt', 'w') as f:
        model.summary(print_fn=lambda x: f.write(x + '\n'))
    #model.summary(print_fn=myprint) # save the model output to txt file

    epochs_range = range(len(val_mae))

    fig = plt.figure(figsize=(20, 10))

    ax1 = fig.add_subplot(1, 3, 1,xscale='log',yscale='log',ylabel='Mean Absolute Error',xlabel='Epoch')
    ax1.plot(epochs_range, val_mae, label='Validation MAE')
    ax1.plot(epochs_range, mae, label='Training MAE')
    ax1.legend(loc='upper right')
    ax1.title.set_text('Training and Validation MAE')


    ax2 = plt.subplot(1, 3, 2,xscale='log',yscale='log',ylabel='Mean Squared Error',xlabel='Epoch')
    ax2.plot(epochs_range, val_mse, label='Validation MSE')
    ax2.plot(epochs_range, mse, label='Training MSE')
    ax2.legend(loc='upper right')
    ax2.title.set_text('Training and Validation MSE')

    ax3 = plt.subplot(1, 3, 3,xscale='log',yscale='log',ylabel='Loss',xlabel='Epoch')

    ax3.plot(epochs_range, val_loss, label='Validation Loss')
    ax3.plot(epochs_range, loss, label='Training Loss')
    ax3.legend(loc='upper right')
    ax3.title.set_text('Training and Validation Loss')

    fig.savefig(str(score_dir)+'/training_history.png') # save

    plt.tight_layout()

    plt.close()

    write.append('\nTEST DATA\n')
    evaluate = model.evaluate(test_ds,test_keys,return_dict=True)
    write.append(evaluate)

    test_predictions = model.predict(test_ds).flatten()

    fig = plt.figure(figsize=(12, 6))
    ax1 = plt.subplot(1,2,1,ylabel='Predictions [angle, degrees]',xlabel='True Values [angle, degrees]',aspect='equal')
    ax1.title.set_text('Test set')
    ax1.scatter(test_keys, test_predictions, c='crimson')
    lims = [0,180]
    _ = plt.plot(lims, lims)

    ax2 = plt.subplot(1,2,2,ylabel='Predictions [angle, degrees]',xlabel='True Values [angle, degrees]',aspect='equal',
                     xlim = [min(test_keys)-1, max(test_keys)+1],ylim = [min(test_predictions)-1, max(test_predictions)+1])
    ax2.title.set_text('Test set')
    ax2.scatter(test_keys, test_predictions, c='crimson')
    lims = [min(test_keys), max(test_keys)]
    _ = plt.plot(lims, lims)

    plt.tight_layout()

    plt.savefig(str(score_dir)+'/test_data.png') # save

    plt.close()

    # output spread of test set error
    err = test_predictions-test_keys
    mu = np.mean(err)  # mean of distribution
    sigma = np.std(err)  # standard deviation of distribution
    num_bins = 50
    fig, ax = plt.subplots()
    n, bins, patches = ax.hist(err, num_bins, density=True) # the histogram of the data

    lower = np.mean(err) - (3*np.std(err))
    upper = np.mean(err) + (3*np.std(err))
    write.append('mean error is '+str.format('{0:.2e}',np.mean(err))+' and standard deviation is '+str.format('{0:.2e}',sigma))
    write.append('99.7% of errors are between '+str(lower)+' and '+(str(upper)))
    # add a 'best fit' line
    y = ((1 / (np.sqrt(2 * np.pi) * sigma)) * np.exp(-0.5 * (1 / sigma * (bins - mu))**2))
    ax.plot(bins, y, '--')
    # add mean and std deviation lines
    ax.axvline(mu,ymax=0.9,color='r')
    for n in [-1,1]:
        ax.axvline(mu+(n*sigma),ymax=0.68*0.9,color='r')
    for n in [-1,1]:
        ax.axvline(mu+(n*2*sigma),ymax=0.05*0.9,color='r')
    for n in [-1,1]:
        ax.axvline(mu+(n*3*sigma),ymax=0.01*0.9,color='r')
    ax.set_xlabel('Error')
    ax.set_ylabel('Frequency')
    ax.set_title(r'Histogram of test set error: $\mu$='+str.format('{0:.2e}', mu)+', $\sigma$='+str.format('{0:.2e}', sigma))

    fig.tight_layout() # Tweak spacing to prevent clipping of ylabel
    plt.savefig(str(score_dir)+'/test_set_spread.png') #save

    plt.close()

    with open(str(score_dir)+'/outputted_data.txt','w') as f:
        for line in write:
            f.write(str(line))
            f.write('\n')

    print('Done')

    return score

def show_result(study):

    pruned_trials = study.get_trials(deepcopy=False, states=[TrialState.PRUNED])
    complete_trials = study.get_trials(deepcopy=False, states=[TrialState.COMPLETE])

    print("Study statistics: ")
    print("  Number of finished trials: ", len(study.trials))
    print("  Number of pruned trials: ", len(pruned_trials))
    print("  Number of complete trials: ", len(complete_trials))

    print("Best trial:")
    trial = study.best_trial

    print("  Value: ", trial.value)

    print("  Params: ")
    for key, value in trial.params.items():
        print("    {}: {}".format(key, value))

def main():

    print("Start time: "+str(datetime.datetime.now()))

    os.environ['TF_FORCE_GPU_ALLOW_GROWTH'] = 'true'

    study_name='contour_test2'
    storage_name = "sqlite:///{}.db".format(study_name)
    study = optuna.create_study(
        study_name=study_name,
        storage=storage_name,
        direction="minimize",
        pruner=optuna.pruners.MedianPruner(n_startup_trials=3),
        load_if_exists=True
    )


    study.optimize(objective, n_trials=1, timeout=345600)#2700 sec is 45 min, 345600 is 4 days

    show_result(study)

if __name__ == "__main__":
    main()
