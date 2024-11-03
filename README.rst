|logo|
======

.. |logo| raw:: html

    <img src="https://opendrop.readthedocs.io/en/latest/_images/opendrop_logo_wide.png" width="185px" alt="Logo">

.. START 

.. image:: https://joss.theoj.org/papers/10.21105/joss.02604/status.svg
    :target: https://doi.org/10.21105/joss.02604

OpenDrop is a fully-featured image analysis software for performing pendant drop tensiometry and contact angle measurements. Images can be loaded from the file system or acquired directly from USB webcams or GenICam (GigE |nbsp| Vision, USB3 |nbsp| Vision) compliant industrial cameras.

.. raw:: html

    <img src="https://raw.githubusercontent.com/jdber1/opendrop/master/screenshots/ift-prepare.png" width="700px" alt="OpenDrop screenshot">

The software is released under the **GNU GPL** open source license, and available for free.

.. |nbsp| unicode:: 0xA0
    :trim:

*********
Background
*********
OpenDrop-ML is an innovative, open-source software project aimed at modernizing contact angle and pendant drop tensiometry in surface science. 
The project addresses the limitations of existing proprietary software, which is often costly and outdated, with some solutions locked to Windows XP.

With OpenDrop-ML, we aim to provide an open-source, cross-platform alternative that leverages machine learning and computer vision to enhance accuracy, autonomy, and ease of use in surface science measurements.


*********
Installation & User Guide
*********
OpenDrop is currently distributed as a Python package and can be installed on most operating systems (Windows, macOS, Linux).

For installation instructions and user guides, visit: https://opendrop.readthedocs.io/

Example images have been provided in the 'example_images' folder.


*********
Software Specification
*********
- **Name:** OpenDrop-ML
- **Languages:** Python
- **License:** GNU GPL Open Source License
- **Supported Platforms:** Windows, macOS, Linux
- **Dependencies:**
  - Python 3.x
  - OpenCV (for image processing)
  - Conan-ML (for machine learning-based analysis)
  - USB webcam or GigE Vision / USB3 Vision compliant cameras (optional)
- **Key Features:**
  - High-precision pendant drop tensiometry and contact angle measurements
  - Integration of Conan-ML for machine learning-based edge and object detection
  - Modular architecture supporting customization and scalability
  - Batch processing for large datasets and video analysis
  - Cross-platform compatibility with a user-friendly interface
Detailed software specifications: Teams files, Requirements folder, OpenDrop Software Specification.doc

*********
Support
*********
For any questions, issues, or feedback feel free to `open an issue on the GitHub repo <https://github.com/jdber1/opendrop/issues>`_.

We can also be contacted by email `here <mailto:opendrop.dev@gmail.com>`_.
