############
Installation
############

**************
Release builds
**************

Stand-alone builds for Windows are provided for certain major releases and do not require the installation of
additional software: https://github.com/jdber1/opendrop/releases/.

Releases for Linux and macOS don't exist yet and OpenDrop should instead be installed as a Python package. See next section.

****************************
Building package from source
****************************

OpenDrop requires Python 3.6 or higher, the GTK 3 library, SCons, and the following build dependencies:

    * Boost.Math
    * SUNDIALS ARKODE

Other required Python packages will be automatically installed by pip. This installation guide will use python3.10 to mitigate broken dependencies.

Platform specific build instructions follow.


Windows
=======

Installing OpenDrop as a Python package is possible on Windows using platforms like MSYS2 or Anaconda.  
The process is not very straightforward so your mileage may vary. We recommend using WSL2 and following the linux installation steps provided below.


Ubuntu (or other Debian-based OS)
=================================

Tested on Ubuntu22.04 using python3.10

#. Update all packages::

       sudo apt-get update


#. Install Python3.10, pip, and scons::

       sudo apt-get install python3.10 python3.10-dev scons
       python3.10 -m ensurepip --upgrade

#. Install build dependencies::

       sudo apt-get install cmake \
           gcc \
           make \
           git \
           wget \
           g++ \
           libglib2.0-dev \
           libcairo2-dev \
           pkg-config \
           libmpich-dev \
           libgtk-3-dev \
           libc6 \
           libgirepository1.0-dev \
           adwaita-icon-theme-full \
           libboost-dev \
           libgtk-3-dev

#. Clean up after installation::
       
       sudo apt-get clean

#. Clone and build v7.1.1 of sundials. Unfortunately, no release existed at time of writing, so we need to install from source. The directory sundials is built in does not matter::

       git clone https://github.com/LLNL/sundials.git
       cd sundials
       git checkout tags/v7.1.1
       mkdir build
       cd build
       cmake ..
       make
       make install

#. Ensure environment variables are properly set::

       export PATH="/usr/local/bin:$PATH"
       export LD_LIBRARY_PATH="/usr/local/lib:/usr/local/lib64:$LD_LIBRARY_PATH"
       ldconfig    

#. Use pip to install OpenDrop from the repo::

       pip3.10 install git+https://github.com/jdber1/opendrop.git

#. Run ``python3.10 -m opendrop`` to launch the app.

Fedora (or other RedHat-based OS)
=================================

Tested on Fedora 35, 40 using python3.10

#. Update all packages::

       sudo dnf update

#. Install Python3.10, pip, and scons::

       sudo dnf install python3.10 python3.10-devel python3-scons
       python3.10 -m ensurepip --upgrade
    
#. Install build dependencies::

       sudo dnf install gcc \
           make \
           git \
           wget \
           glibc \
           cmake \
           gcc-c++ \
           glib2-devel \
           cairo-devel \
           pkgconfig \
           cairo-gobject-devel \
           gobject-introspection-devel \
           mpich-devel \
           gtk3-devel \
           boost-devel

#. Clean up after installation::
       
       sudo dnf clean all

#. Clone and build v7.1.1 of sundials. Unfortunately, no release existed at time of writing, so we need to install from source. The directory sundials is built in does not matter::

       git clone https://github.com/LLNL/sundials.git
       cd sundials
       git checkout tags/v7.1.1
       mkdir build
       cd build
       cmake ..
       make
       make install

#. Ensure environment variables are properly set::

       export PATH="/usr/local/bin:$PATH"
       export LD_LIBRARY_PATH="/usr/local/lib:/usr/local/lib64:$LD_LIBRARY_PATH"
       ldconfig    

#. Use pip to install OpenDrop from the repo::

       pip3.10 install git+https://github.com/jdber1/opendrop.git

#. Run ``python3.10 -m opendrop`` to launch the app.
         

macOS
=====

#. Install Python3.10, scons and other build dependencies using a third-party package manager like Homebrew_ or MacPorts_::

       brew install python@3.10 scons glib cairo pkg-config gtk+3 mpich cmake boost git wget

       sudo port install python310 scons glib2 cairo pkgconfig gtk3 mpich cmake boost git wget

#. Clone and build v7.1.1 of sundials. Unfortunately, no release existed at time of writing, so we need to install from source. The directory sundials is built in does not matter::

       git clone https://github.com/LLNL/sundials.git
       cd sundials
       git checkout tags/v7.1.1
       mkdir build
       cd build
       cmake ..
       make
       make install

#. Ensure environment variables are properly set::

       export PATH="/usr/local/bin:$PATH"
       export LD_LIBRARY_PATH="/usr/local/lib:/usr/local/lib64:$LD_LIBRARY_PATH"
       ldconfig    

#. Use pip to install OpenDrop from the repo::

       pip3.10 install git+https://github.com/jdber1/opendrop.git

#. Run ``python3.10 -m opendrop`` to launch the app.

#. If you encounter this issue: 'boost/math/differentiation/autodiff.hpp' file not found. Find the install directory of boost, copy the path and add it to the env variable as follows:

       find /opt/ -name  "*.hpp" | grep boost

       # Copy the path to the file without the file name
       export BOOST_INCLUDE_DIR=path

.. _opencv-python: https://pypi.org/project/opencv-python/
.. _MacPorts: https://www.macports.org/
.. _Homebrew: https://brew.sh/
