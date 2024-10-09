# print data and time to denote start
date
echo "Generating contours"

mkdir -p contour_dataset_4par/

# Run python file in parallel piping the angle to %, and defining the roughness value in each line
# -P term may need altering if running on HPC systems
seq 110 0.02 180 | xargs -n 1 -P 0 -t -I % python3 create_contours_args4.py ./contour_dataset_4par/ -a %  -r 0.0
seq 110 0.02 180 | xargs -n 1 -P 0 -t -I % python3 create_contours_args4.py ./contour_dataset_4par/ -a %  -r 0.002
seq 110 0.02 180 | xargs -n 1 -P 0 -t -I % python3 create_contours_args4.py ./contour_dataset_4par/ -a %  -r 0.004
seq 110 0.02 180 | xargs -n 1 -P 0 -t -I % python3 create_contours_args4.py ./contour_dataset_4par/ -a %  -r 0.006
seq 110 0.02 180 | xargs -n 1 -P 0 -t -I % python3 create_contours_args4.py ./contour_dataset_4par/ -a %  -r 0.008
seq 110 0.02 180 | xargs -n 1 -P 0 -t -I % python3 create_contours_args4.py ./contour_dataset_4par/ -a %  -r 0.01
seq 110 0.02 180 | xargs -n 1 -P 0 -t -I % python3 create_contours_args4.py ./contour_dataset_4par/ -a %  -r -0.06
seq 110 0.02 180 | xargs -n 1 -P 0 -t -I % python3 create_contours_args4.py ./contour_dataset_4par/ -a %  -r -0.04
seq 110 0.02 180 | xargs -n 1 -P 0 -t -I % python3 create_contours_args4.py ./contour_dataset_4par/ -a %  -r -0.02

# print date and time to denote end
date
echo "Combining to a single file"

python3 combine.py

# print date and time to denote end
echo "Zero-padding data set"

python3 zeropad.py

#print date and time to denote end
date
