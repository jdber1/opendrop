###############
Getting Started
###############

************
Installation
************

OpenDrop runs on Python 3.5+, and uses PyGObject's GTK bindings for the user interface, and OpenCV for image analysis.

Installation instructions for some platforms have been provided below.

Ubuntu 16.04+/Debian 9+
=======================

#. * The unofficial opencv-python_ package can be installed using pip and is the easiest way to install the required OpenCV functionalities.
   * Alternatively, if on Ubuntu 17.10 (or later), the ``python3-opencv`` package is also available from the 'Universe' repository and can be installed with::

       sudo apt install python3-opencv

#. Follow the `installation instructions here <https://pygobject.readthedocs.io/en/latest/getting_started.html#ubuntu-logo-ubuntu-debian-logo-debian>`_ for installing PyGObject and GTK.

#. Use pip to install Opendrop from the repository by running::

       pip install git+https://github.com/jdber1/opendrop.git@development

   (You may need to use ``pip3`` to refer to the Python 3 version.)

   Run ``pip uninstall opendrop`` to uninstall.

#. An ``opendrop`` script is installed into your PATH and the app can be launched by entering ``opendrop`` in the command line.


macOS
=====

1. Install the latest version of Python 3 and pip. You may like to do so using a package manager like MacPorts_ or Homebrew_.

2. - Install the unofficial opencv-python_ package by running::

         pip install opencv-python

     (Make sure ``pip`` refers to your Python 3's pip installation.)
   - Alternatively, OpenCV and its python bindings can also be installed using the `opencv Homebrew formula <https://formulae.brew.sh/formula/opencv>`_ or `opencv MacPorts port <https://www.macports.org/ports.php?by=library&substr=opencv>`_.

3. - If Homebrew was used to install Python 3, PyGObject and GTK can also be installed by running::

         brew install pygobject3 gtk+3

   - or if MacPorts was used, run::

         sudo port install py35-gobject3 gtk3

     (Instead of the ``py35-`` prefix, use ``py36-`` or ``py37-`` if Python 3.6/3.7 is the version installed.)

4. Use pip to install OpenDrop from the repository by running::

       pip install git+https://github.com/jdber1/opendrop.git@development

   Run ``pip uninstall opendrop`` to uninstall.

5. An ``opendrop`` script is installed into your PATH and the app can be launched by entering ``opendrop`` in the command line.


.. _opencv-python: https://pypi.org/project/opencv-python/
.. _MacPorts: https://www.macports.org/
.. _Homebrew: https://brew.sh/
