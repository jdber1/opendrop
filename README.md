# Conan-ML

Conan-ML software is a tool engineered for precise and automated
processing and analysis of contact angle data. The software utilizes image
processing algorithms to analyze captured images of droplets on surfaces.
Current implementation is only optimised for high angle systems. More information
about the method and accuracy is available here: 
https://doi.org/10.1021/acs.langmuir.4c01050

# Dependencies

Conan-ML is written to run on python3.6+. The packages required to run
conan ML must be installed in your Python environment. These are included
listed in requirements.txt and can be install using

pip install -r requirements.txt

# Usage

To load  Conan-ML GUI run the conan.py file using

python conan.py

However, functions from each file of the modules directory can be called
for a more customised approach.

# Appropriate use

This section has been included as many users of Conan-ML will not be familiar
with the use of ML models and their limitations and best practice use cases.

The key limitation of ML models is that accuracy may deteriorate when used
on systems which was not represented within it's training data. While it has
been shown that the model can be applied to systems of contact angles below
110°, caution should be applied applied in these cases. It is recommended that
contact angles are plotted and briefly examined (i.e. sense-checked) as
general practice, but particularly for systems outside of training domain.
Similarly, drops with Bond numbers greater than 2 were not included in the
training set and should be approached with caution.

Surface roughness and reflection were included to train the model to ignore
inputted data which is not the drop edge. However, few images with surface
roughness which deviated from the training data were included in the
experimental data set. As such users are again advised to check outputs
for systems outside of the training range.

As the resolution of an image can be altered, should the resolution of an
image be too high it will be lowered to give an input suitable for the
ML model. This is the only exception to the above limitations.

High quality edge detection should be used to achieve the best results.
This work presents an automated process, which still requires improvement,
but will likely be suitable for high contrast images. Users are recommended
to check that the detected edge is reasonable prior to accepting the results
outputted by any fitting or angle prediction approach.
