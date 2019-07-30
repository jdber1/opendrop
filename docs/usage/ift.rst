Interfacial Tension
===================

A wizard-style window will guide you through the process of performing an interfacial tension analysis.

Image acquisition
-----------------

First, choose an image input method. OpenDrop currently supports opening images from the local filesystem or capturing images with a USB camera.

Local filesystem
^^^^^^^^^^^^^^^^

.. image:: images/ift_local_filesystem.png
    :alt: IFT Image acquisition, local filesystem
    :width: 914
    :align: center

Click on 'Choose files' to open the file chooser dialog and select an individual image or a sequence of images. When analysing a sequence of images, 'Frame interval' refers to the time interval (in seconds) between each image. Sequences of images are ordered in lexicographic order.

USB camera
^^^^^^^^^^

.. image:: images/ift_usb_camera.png
    :alt: IFT Image acquisition, USB camera
    :width: 914
    :align: center

Click on 'Connect camera' to open the camera chooser dialog.

.. image:: images/ift_usb_camera_camera_chooser.png
    :alt: IFT Image acquisition, USB camera chooser dialog
    :width: 828
    :align: center

OpenDrop uses OpenCV to capture images from a connected camera. 'Camera index' refers to the device index argument passed to the OpenCV function ``cv2.VideoCapture()``. An index of 0 refers to the first connected camera (usually a laptop's in-built webcam if present), an index of 1 refers to the second camera, and so on. Currently, there does not appear to be a way in OpenCV to query a list of valid device indices and associated device names, so in a multi-camera setup, some trial-and-error is required.

'Frame interval' refers to the time interval (in seconds) between capturing images.


Physical parameters
-------------------

.. image:: images/ift_physical_parameters.png
    :alt: IFT Physical parameters
    :width: 914
    :align: center


'Inner density' refers to the density of the drop.

'Outer density' refers to the density of the surrounding medium.

'Needle diameter' refers to the diameter of the needle the drop is suspended from.

'Gravity' refers to the gravitational acceleration.


Image processing
----------------

.. image:: images/ift_image_processing.png
    :alt: IFT Image processing
    :width: 914
    :align: center

The image processing window requires you to define the 'drop region' and 'needle region' of the image. Click on the 'Drop region' or 'Needle region' buttons in the 'Tools' panel, then drag over the image preview to define the associated region.

.. image:: images/ift_image_processing_regions_defined.png
    :alt: IFT Image processing, regions defined
    :width: 914
    :align: center

Once each region is defined, a blue outline will be drawn over the preview showing the drop or needle profile that has been extracted.

OpenDrop uses OpenCV's Canny edge detector to detect edges in the image, click on the 'Edge detection' button in the 'Tools' panel to open a dialog bubble which will allow you to adjust the lower and upper threshold parameters of the Canny edge detector. Thin blue lines are drawn over the preview to show detected edges.

The extracted needle profile is used to determine the diameter in pixels of the needle in the image. Along with the needle diameter in millimetres given in the 'Physical parameters' page, a metres-per-pixel scale can be determined, which is then used to derive other physical properties of the drop after the image is analysed.

Click on 'Start analysis' to begin analysing the input images, or begin capturing and analysing images if using a camera.


Results
-------

.. image:: images/ift_results.png
    :alt: IFT Results
    :width: 914
    :align: center

The results page shows the current status of the analysis. Data shown in the window is updated as the analysis progresses.

There are two main views, the 'Individual Fit' view and the 'Graphs' view. The 'Graphs' view is not available when analysing a single image.

Individual Fit
^^^^^^^^^^^^^^

The 'Individual Fit' view shows analysis details for an individual image. Pick an analysis in the lower panel to preview its details in the upper panel.

.. image:: images/ift_results_drop_profile.png
    :alt: IFT Results, drop profile
    :width: 591
    :align: center

The 'Drop profile' tab on the right of the upper panel shows the fitted drop profile (drawn in magenta) over the extracted drop profile (drawn in blue).

.. image:: images/ift_results_fit_residuals.png
    :alt: IFT Results, fit residuals
    :width: 591
    :align: center

The 'Fit residuals' tab shows a plot of the fit residuals. The horizontal axis is the 'drop profile parameter', ranging from 0 to 1, with 0 corresponding to one end of the drop edge outline, and 1 corresponding to the other end. The vertical axis is some dimensionless quantity indicating the deviation of the extracted profile from the fitted profile.

.. image:: images/ift_results_log.png
    :alt: IFT Results, log
    :width: 591
    :align: center

The 'Log' tab shows the history of any messages logged by the fitting routine.

Graphs
^^^^^^

.. image:: images/ift_results_graphs.png
    :alt: IFT Results, graphs
    :width: 914
    :align: center

The 'Graphs' view shows plots of interfacial tension, volume, and surface area over time.

Cancel or discard analysis
^^^^^^^^^^^^^^^^^^^^^^^^^^

You may cancel an in progress analysis by clicking on the 'Cancel' button in the footer (not shown in the screenshots above). To discard the results of a finished analysis, click the 'Back' button, which will return you to the 'Image processing' page, or close the window to return to the Main Menu.


Saving
------

.. image:: images/ift_save_dialog.png
    :alt: IFT Save dialog
    :width: 828
    :align: center

Once an analysis is finished, click on the 'Save' button in the footer to open the save dialog. All data will be saved in a folder with name determined by the 'Name' entry, and in a parent directory determined by the 'Parent' selection. 

As a convenience, you may choose to save some pre-made plots.

.. image:: images/ift_save_output.png
    :alt: IFT Example save output
    :width: 662
    :align: center

An example save output is shown above, and screenshots of the contents of some files are shown below.

.. figure:: images/ift_timeline_csv.png
    :alt: IFT timeline.csv screenshot
    :width: 1000
    :align: center

    timeline.csv

.. figure:: images/ift_profile_fit_csv.png
    :alt: IFT profile_fit.csv screenshot
    :width: 159
    :align: center

    water_in_air1/profile_fit.csv (each row is an (x, y) coordinate pair)

.. figure:: images/ift_profile_extracted_csv.png
    :alt: IFT profile_extracted.csv screenshot
    :width: 159
    :align: center

    water_in_air1/profile_extracted.csv (each row is an (x, y) coordinate pair)

.. figure:: images/ift_profile_fit_residuals_csv.png
    :alt: IFT profile_fit_residuals.csv screenshot
    :width: 159
    :align: center

    water_in_air1/profile_fit_residuals.csv (first column is 'drop profile parameter', second column is residual)

.. figure:: images/ift_params_ini.png
    :alt: IFT params.ini screenshot
    :width: 485
    :align: center

    water_in_air1/params.ini
