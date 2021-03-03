############
Installation
############

**************
Release Builds
**************

Stand-alone builds for Windows are provided for certain major releases and do not require the installation of
additional software: https://github.com/jdber1/opendrop/releases/.

Releases for Linux and macOS don't exist yet and OpenDrop should instead be installed as a Python package. See next section.

****************************
Building package from source
****************************

OpenDrop requires Python 3.6 or higher, the GTK 3 library, OpenCV Python bindings, and the following build dependencies:

    * Boost.Math
    * SUNDIALS ARKODE

Other required Python packages will be automatically installed by pip.

Platform specific build instructions follow.


Ubuntu 16.04+/Debian 9+
=======================

#. Install OpenCV.

   * If on Ubuntu 17.10 (or later)::

       sudo apt install python3-opencv

   * Alternatively there is an unofficial opencv-python_ package that can be installed using pip::
       
       pip3 install opencv-python


#. Install Boost.Math and SUNDIALS::

       sudo apt install libboost-math-dev libsundials-dev

#. Follow the `installation instructions here <https://pygobject.readthedocs.io/en/latest/getting_started.html#ubuntu-logo-ubuntu-debian-logo-debian>`_ for installing PyGObject and GTK.

#. Use pip to install OpenDrop from the repo::

       pip3 install git+https://github.com/jdber1/opendrop.git

   Run ``pip3 uninstall opendrop`` to uninstall.

#. Run ``python3 -m opendrop`` to launch the app.


macOS
=====

1. Install the latest version of Python 3 and pip. You can do so using a third-party package manager like MacPorts_ or Homebrew_.

2. - Install the unofficial opencv-python_ package by running::

         pip install opencv-python

     (Make sure ``pip`` refers to your Python 3's pip installation.)
   - Alternatively, OpenCV and its python bindings can also be installed using the `opencv Homebrew formula <https://formulae.brew.sh/formula/opencv>`_ or `opencv MacPorts port <https://www.macports.org/ports.php?by=library&substr=opencv>`_.

3. - If Homebrew was used to install Python 3, PyGObject and GTK can also be installed by running::

         brew install pygobject3 gtk+3

   - or if MacPorts was used, run::

         sudo port install py36-gobject3 gtk3

     (Instead of the ``py36-`` prefix, use ``py37-`` or ``py38-`` if Python 3.7/3.8 is the version installed.)

#. Install Boost.Math and SUNDIALS. (todo: Add MacPorts and Homebrew example).

4. Use pip to install OpenDrop from the repo::

       pip install git+https://github.com/jdber1/opendrop.git

   Run ``pip uninstall opendrop`` to uninstall.

5. Run ``python3 -m opendrop`` to launch the app.


Windows
=======

Installing OpenDrop as a Python package is possible on Windows using platforms like MSYS2 or Anaconda.  
The process is not very straightforward so your mileage may vary.


.. _opencv-python: https://pypi.org/project/opencv-python/
.. _MacPorts: https://www.macports.org/
.. _Homebrew: https://brew.sh/
