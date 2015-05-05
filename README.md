OpenDrop README
===============


Release notes and license
=========================

OpenDrop is released under the GNU GPL License. You are free to modify and distribute the code, but always under the same license (i.e. you cannot make commercial derivatives).

If you use this software in your research, please cite the following journal article:

J. D. Berry, M. J. Neeson, R. R. Dagastine, D. Y. C. Chan and R. F. Tabor,
Measurement of surface and interfacial tension using pendant drop tensiometry.
Journal of Colloid and Interface Science (2015)

These citations help us not only to understand who is using and developing OpenDrop, and for what purpose, but also to justify continued development of this code and other open source resources.


Contents
========

0) Operating system

1) Installation

2) Image source selection

3) Running measurements

4) Appendix A: preparing Ubuntu for OpenDrop

5) Appendix B: preparing FlyCap2 for using Point Grey cameras




0. Operating system:
--------------------
In the spirit of its open source and free nature, OpenDrop is recommended for use with Linux, and has been extenstively tested on Ubuntu 14.04 LTS.

OpenDrop works well on Mac OSX, provided that Python and OpenCV libraries are successfully installed.

It has not been tested on Windows or other operating systems

1. Installation:
----------------
OpenDrop itself does not require installation. Simply place the files and modules folder in a suitable location on your computer. 

OpenDrop has dependencies on the following resources/libraries:
- Python
- OpenCV

If not contained within the Python/OpenCV installation method that you choose, also required are:
- Python-scipy
- Python-matplotlib
- Python-numpy

Make sure these are installed for your operating system before running OpenDrop. See Appendix A for how to prepare a fresh installation of Ubuntu 14.04 for OpenDrop.

2. Image source selection:
--------------------------
OpenDrop can currently utilise images from three sources:
a) Point Grey cameras (Linux/Windows - the script supplied is for Linux, but a Windows script of the same name could also be used). An installation guide for getting these set up under Ubuntu is provided in Appendix B. OpenDrop has been tested with Flea3 USB cameras.
b) USB camera (currently Linux/Mac only). Selecting this option will utilise the primary camera, i.e. the one listed as "camera0". Use of a regular USB camera with Windows is no doubt possible, but has not been tested.
c) Local images (all operating systems). This option allows a user to select a locally stored image file for fitting.

3. Running measurements:
------------------------
For Ubuntu, the OpenDrop.py file can be made "double-clickable" by changing the default Nautilus preferences (Edit --> Preferences --> Behaviour). Alternatively, running:
>  ./bashme 

in a terminal will provide a verbose terminal and run the program.

A window will appear requiring input for system parameters such as image source, needle diameter, droplet and continuous phase density, etc. The selection items should be fairly obvious. Boxes will be recalled from previous values after the first use.

Once the settings have been suitably adjusted, select "Run". This should capture/open an image from the selected source, and bring up an OpenCV window containing this window. As requested, draw boxes over the desired fitting area of the drop, and a section of the needle that is representative and clear from contamination/aberrations. After each selection, press either the "enter" or "space" key. 

The automated fitting routine will then commence. A file is created with the specified name and a date-time stamp containing the fitted data.



Appendix A
==========

Preparing Ubuntu 14.04 for OpenDrop.
------------------------------------

The following commands typed into the terminal will prepare an installation of Ubuntu 14.04.01 for OpenDrop, installing all required libraries and fixing dependencies. An unresolvable conflict (that may have since been corrected) was encountered when trying this process with 14.04.02.

> sudo apt-get update

> sudo apt-get upgrade

> sudo apt-get install build-essential libgtk2.0-dev libjpeg-dev libtiff4-dev libjasper-dev libopenexr-dev cmake python-dev python-numpy python-tk libtbb-dev libeigen3-dev yasm libfaac-dev libopencore-amrnb-dev libopencore-amrwb-dev libtheora-dev libvorbis-dev libxvidcore-dev libx264-dev libqt4-dev libqt4-opengl-dev sphinx-common texlive-latex-extra libv4l-dev libdc1394-22-dev libavcodec-dev libavformat-dev libswscale-dev default-jdk ant libvtk5-qt4-dev

> sudo apt-get install python-scipy

> sudo apt-get install python-matplotlib

> cd ~

> wget http://sourceforge.net/projects/opencvlibrary/files/opencv-unix/2.4.9/opencv-2.4.9.zip

> unzip opencv-2.4.9.zip

> cd opencv-2.4.9

> mkdir build

> cd build

> cmake -D WITH_TBB=ON -D BUILD_NEW_PYTHON_SUPPORT=ON -D WITH_V4L=ON -D INSTALL_C_EXAMPLES=ON -D INSTALL_PYTHON_EXAMPLES=ON -D BUILD_EXAMPLES=ON -D WITH_QT=ON -D WITH_OPENGL=ON -D WITH_VTK=ON ..

> make

> sudo make install

> sudo gedit /etc/ld.so.conf.d/opencv.conf

and add line 
/usr/local/lib

> sudo ldconfig

> sudo gedit /etc/bash.bashrc

and add lines
PKG_CONFIG_PATH=$PKG_CONFIG_PATH:/usr/local/lib/pkgconfig
export PKG_CONFIG_PATH
close the console and open a new one, restart the computer or logout and then login again.


Appendix B
==========

Installing and preparing FlyCap2 software and libraries for using Point Grey cameras on Ubuntu 14.04:
-----------------------------------------------------------------------------------------------------
Download the latest FlyCap2 from https://www.ptgrey.com/support/downloads (login required) - tested using 2.7.3.13

> sudo apt-get install glade

> sudo apt-get install libraw1394-11 libgtk2.0-0 libgtkmm-2.4-dev libglademm-2.4-dev libgtkglextmm-x11-1.2-dev libusb-1.0-0

Unpack the FlyCap2 zip, and find your way into the directory. Run:

> sh install_flycapture.sh

To make the FCGrab script:

Copy the FlyCapture_building directory from Dropbox to somewhere convenient
Move into /src/FCGrab
> make

