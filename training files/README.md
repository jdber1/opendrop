# Create the training data set
- create_dataset_parallel.sh: Run this to initiate the creation of the training data set. Using this allows for parallel CPU usage and so accelerates data generation
- create_contours_args4.py: This is the code used to create training contours, called by create_dataset_parallel.sh
- combine.py: Combines the many files created by create_contours_args4.py into a single file, called by create_dataset_parallel.sh
- zeropad.py: Zero-pads all contours to the maximum contour length of the data set, called by create_dataset_parallel.sh

# Train the model
- train.sh: Run this to initiate the training on the model once training data has been generated
- train_model.py: This is the code used to train the model, called by train.sh. To continue training after if it does not finish in the desired time, weights.best.hdf5 can be loaded instead of creating a new model in the objective function.

