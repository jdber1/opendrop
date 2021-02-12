###############
Getting Started
###############

******************************
Installing as a Python package
******************************

Ubuntu 16.04+/Debian 9+
=======================

#. * The unofficial opencv-python_ package can be installed using pip and is the easiest way to install the required OpenCV functionalities.
   * Alternatively, if on Ubuntu 17.10 (or later), the ``python3-opencv`` package is also available from the 'Universe' repository and can be installed with::

       sudo apt install python3-opencv

#. Follow the `installation instructions here <https://pygobject.readthedocs.io/en/latest/getting_started.html#ubuntu-logo-ubuntu-debian-logo-debian>`_ for installing PyGObject and GTK.

#. Use pip to install OpenDrop from the repo::

       pip install git+https://github.com/jdber1/opendrop.git

   (You may need to use ``pip3`` to refer to the Python 3 version.)

   Run ``pip uninstall opendrop`` to uninstall.

#. Run ``python3 -m opendrop`` to launch the app.


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

         sudo port install py36-gobject3 gtk3

     (Instead of the ``py36-`` prefix, use ``py37-`` or ``py38-`` if Python 3.7/3.8 is the version installed.)

4. Use pip to install OpenDrop from the repo::

       pip install git+https://github.com/jdber1/opendrop.git

   Run ``pip uninstall opendrop`` to uninstall.

5. Run ``python3 -m opendrop`` to launch the app.


******************************
Windows
******************************

Installing OpenDrop as a Python package is possible on Windows using the likes of MSYS2 or Anaconda but the
process is not very straight forward.

Stand-alone binaries for Windows are provided for certain major releases and do not require the installation of
additional software: https://github.com/jdber1/opendrop/releases/.


.. _opencv-python: https://pypi.org/project/opencv-python/
.. _MacPorts: https://www.macports.org/
.. _Homebrew: https://brew.sh/
