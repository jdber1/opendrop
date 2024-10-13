# import libraries
import pickle5 as pickle
import matplotlib.pyplot as plt

# define paths and flags
src = './output_post_loadedweights.txt'
file1 = open(src,"rb")

parse_to_pkl = False

check_history_save = True

generate_plots = True
show_restart_points = True
display = False
save_path = './training_history_all.png' # set to None if not saving

if parse_to_pkl: # save history to pkl file
    history = {}
    loss = []
    mae = []
    mse = []
    val_loss = []
    val_mae = []
    val_mse = []
    restart_points = []

    for i, line in enumerate(file1):
        line = str(line)
        #if i<15:
        if 1:
            if 'dataset loaded...' in line:
                restart_point = True
            if '/step' in line and 'val_mean_squared_error' in line:
                loss.append(eval(line.split(' ')[-16]))
                mae.append(eval(line.split(' ')[-13]))
                mse.append(eval(line.split(' ')[-10]))
                val_loss.append(eval(line.split(' ')[-7]))
                val_mae.append(eval(line.split(' ')[-4]))
                val_mse.append(eval(line.split(' ')[-1][:-3]))

                if restart_point == True:
                    restart_points.append(len(mae))
                    restart_point = False
            #if 'Epoch' in line:
                #print(line.split(' '))
        else:
            break

    history = {'loss': loss,
               'mean_absolute_error': mae,
               'mean_squared_error': mse,
               'val_loss': val_loss,
               'val_mean_absolute_error': val_mae,
               'val_mean_squared_error': val_mse,
               'restart_points': restart_points}

    with open('history' + '.pkl', 'wb') as f:
        pickle.dump(history, f, pickle.HIGHEST_PROTOCOL)

if check_history_save: #check history save
    def load_obj(name ):
        with open(name + '.pkl', 'rb') as f:
            return pickle.load(f)

    history = load_obj('history')
    print('history keys: ', history.keys())
    print(history)
    for key in history.keys():
        print(key+' shape: '+str(len(history[key])))

if generate_plots: # generate plots using data

    import matplotlib.pyplot as plt

    def load_obj(name ):
        with open(name + '.pkl', 'rb') as f:
            return pickle.load(f)

    history = load_obj('history')

    mae = history['mean_absolute_error']
    val_mae = history['val_mean_absolute_error']

    mse = history['mean_squared_error']
    val_mse = history['val_mean_squared_error']

    loss = history['loss']
    val_loss = history['val_loss']

    restart_points = history['restart_points']

    if 0: #check lists
        print(mae)
        for thing in mae:
            if thing > 10:
                print(thing)

    epochs_range = range(len(history['loss']))#range(epochs)

    plt.figure(figsize=(20, 10))

    plt.subplot(1, 3, 1)
    plt.plot(epochs_range, val_mae, label='Validation MAE')
    plt.plot(epochs_range, mae, label='Training MAE')
    if show_restart_points == True:
        for i, point in enumerate(restart_points):
            if i==0:
                plt.plot([point,point], [min(mae),max(mae)],'r',label='Restart Points')
            else:
                plt.plot([point,point], [min(mae),max(mae)],'r')
    plt.legend(loc='upper right')
    plt.title('Training and Validation MAE\nFinal training MAE: '+str(mae[-1])+'\nFinal val MAE: '+str(val_mae[-1]))
    plt.yscale('log')
    plt.xscale('log')
    plt.ylabel('Mean Absolute Error')
    plt.xlabel('Epoch')

    plt.subplot(1, 3, 2)
    plt.plot(epochs_range, val_mse, label='Validation MSE')
    plt.plot(epochs_range, mse, label='Training MSE')
    if show_restart_points == True:
        for i, point in enumerate(restart_points):
            if i==0:
                plt.plot([point,point], [min(mse),max(mse)],'r',label='Restart Points')
            else:
                plt.plot([point,point], [min(mse),max(mse)],'r')
    plt.legend(loc='upper right')
    plt.title('Training and Validation MSE')
    plt.title('Training and Validation MSE\nFinal training MSE: '+str(mse[-1])+'\nFinal val MSE: '+str(val_mse[-1]))
    plt.yscale('log')
    plt.xscale('log')
    plt.ylabel('Mean Squared Error')
    plt.xlabel('Epoch')

    plt.subplot(1, 3, 3)


    plt.plot(epochs_range, val_loss, label='Validation Loss')
    plt.plot(epochs_range, loss, label='Training Loss')
    if show_restart_points == True:
        for i, point in enumerate(restart_points):
            if i==0:
                plt.plot([point,point], [min(loss),max(loss)],'r',label='Restart Points')
            else:
                plt.plot([point,point], [min(loss),max(loss)],'r')
    plt.legend(loc='upper right')
    plt.title('Training and Validation Loss')
    plt.title('Training and Validation loss\nFinal training loss: '+str(loss[-1])+'\nFinal val loss: '+str(val_loss[-1]))
    plt.yscale('log')
    plt.xscale('log')
    plt.ylabel('Loss')
    plt.xlabel('Epoch')
    if display == True:
        plt.show()

    if save_path != None:
        plt.savefig(save_path, format='png')
    plt.close()

print('done')
