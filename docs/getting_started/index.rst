###############
Getting Started
###############

************
Installation
************

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

Windows 10
=======================
1. Download and nstall Anaconda Python 3.7 from here: https://www.anaconda.com/distribution/

2. Open the Anaconda prompt and install opencv with the command::

    conda install -c conda-forge opencv

When you are asked if you want to proceed, press enter to install opencv and its dependencies.

3. Install pygobject using conda with::

    conda install -c conda-forge pygobject
    
4. Install git using conda with::

    conda install -c anaconda git
    
5. Now type the following command to install opendrop::
    
    pip install git+https://github.com/jdber1/opendrop.git@development
    
6. Type ``opendrop`` to run the program 

Oh no! Error! See below::

    (base) C:\Users\dkarra>opendrop
    Traceback (most recent call last):
    File "c:\users\dkarra\appdata\local\continuum\anaconda3\lib\runpy.py", line 193, in _run_module_as_main
    "__main__", mod_spec)
    File "c:\users\dkarra\appdata\local\continuum\anaconda3\lib\runpy.py", line 85, in _run_code
    exec(code, run_globals)
    File "C:\Users\dkarra\AppData\Local\Continuum\anaconda3\Scripts\opendrop.exe\__main__.py", line 5, in <module>
    File "c:\users\dkarra\appdata\local\continuum\anaconda3\lib\site-packages\opendrop\app\__init__.py", line 1, in <module>
    import gi
    File "c:\users\dkarra\appdata\local\continuum\anaconda3\lib\site-packages\gi\__init__.py", line 42, in <module>
    from . import _gi
    ImportError: DLL load failed: The specified procedure could not be found.
    
    
1. Now trying the 'Windows subsystem for Linux' feature now (installation instructions here: 
https://docs.microsoft.com/en-us/windows/wsl/install-win10)

- Activate the feature using Windows Powershell (run as administrator)
- Restart computer
- Install Ubuntu 18.04 LTS from Microsoft Store
- Launch an Ubuntu session
- One installed, you will need to enter your username and password
- sudo apt-get update
- sudo apt-get upgrade
- Follow instructions for ubuntu installation above (you may also need to install pip3 using sudo apt install python3-pip)
- Close the Ubuntu window
- Download Xming from here: https://sourceforge.net/projects/xming/
- Install Xming, accepting all the default options 
- Open Ubuntu session, run opendrop

WSL doesn't support hardware yet - can't use camera live window


.. _opencv-python: https://pypi.org/project/opencv-python/
.. _MacPorts: https://www.macports.org/
.. _Homebrew: https://brew.sh/
