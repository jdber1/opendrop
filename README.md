# Release notes and license

OpenDrop is released under the GNU GPL License. You are free to modify and distribute the code, but always under the same license (i.e. you cannot make commercial derivatives).

If you use this software in your research, please cite the following journal article:

J. D. Berry, M. J. Neeson, R. R. Dagastine, D. Y. C. Chan and R. F. Tabor,
Measurement of surface and interfacial tension using pendant drop tensiometry.
Journal of Colloid and Interface Science (2015)
```
@Article{OpenDrop:2015,
  Author    = {Berry, J.D. and Neeson, M.J. and Dagastine, R.R. and Chan, D.Y.C. and Tabor, R.F.},
  Title     = {Measurement of surface and interfacial tension using pendant drop tensiometry},
  Journal   = {Journal of Colloid and Interface Science},
  Volume    = {},
  Number    = {},
  Pages     = {},
  month     = may,
  year      = 2015,
  doi       = {10.1016/j.jcis.2015.05.012},
}
```
These citations help us not only to understand who is using and developing OpenDrop, and for what purpose, but also to justify continued development of this code and other open source resources.

If you find any bugs, require assistance, or have implemented improvements/extensions, please [email](mailto:opendrop.dev@gmail.com) us.

To view the OpenDrop manual, click [here](http://nbviewer.ipython.org/github/jdber1/opendrop/blob/master/manual/manual.ipynb).


# Contents

[1. Operating system](#operating-system)

[2. Installation](#installation)

[3\. Image source selection](#image-source-selection)

[4\. Running measurements](#running-measurements)

[5\. Version 2 changes](#version-2-changes)

[6\. Consant volume mode](#constant-volume-mode)

[Appendix A: preparing Ubuntu for OpenDrop](#appendix-a)

[Appendix B: upgrading from OpenDrop v1 to OpenDrop v2](#appendix-b)

[Appendix C: preparing Windows for OpenDrop](#appendix-c)

[Appendix D: preparing Mac OSX for OpenDrop](#appendix-d)

[Appendix E: preparing FlyCap2 for using Point Grey cameras](#appendix-e)


# Operating system:

In the spirit of its open source and free nature, OpenDrop is recommended for use with Linux, and has been extenstively tested on Ubuntu 14.04 LTS.

OpenDrop also works on Mac OSX and Windows, provided that Python and OpenCV libraries are successfully installed, however this has not been extensively tested.


# Installation:

OpenDrop itself does not require installation. Simply place the files and modules folder in a suitable location on your computer.

OpenDrop has dependencies on the following resources/libraries:
- Python
- OpenCV

If not contained within the Python/OpenCV installation method that you choose, also required are:
- Python-scipy
- Python-matplotlib
- Python-numpy

Make sure these are installed for your operating system before running OpenDrop. See Appendix A for how to prepare a fresh installation of Ubuntu 14.04 for OpenDrop, Appendix B for installation on Windows 7, and Appendix C for installation on Mac OSX.


# Image source selection:

OpenDrop can currently utilise images from three sources:
  * Point Grey cameras (Linux/Windows - the script supplied is for Linux, but a Windows script of the same name could also be used). An installation guide for getting these set up under Ubuntu is provided in Appendix D. OpenDrop has been tested with Flea3 USB cameras.
  * USB camera (currently Linux/Mac, appears to also work on Windows 7). Selecting this option will utilise the primary camera, i.e. the one listed as "camera0". a
  * Local images (all operating systems). This option allows a user to select a locally stored image file for fitting.


# Running measurements:

For Ubuntu, the OpenDrop.py file can be made "double-clickable" by changing the default Nautilus preferences (Edit --> Preferences --> Behaviour). Similarly, so can the more universal "run" file. If your operating system is setup for this behaviour, simply double-click "run" to start the software.

Alternatively, running:

```
./run
```

in a terminal will provide a verbose terminal and run the program.

A window will appear requiring input for system parameters such as image source, needle diameter, droplet and continuous phase density, etc. The selection items should be fairly obvious. Boxes will be recalled from previous values after the first use.

Once the settings have been suitably adjusted, select "Run". This should capture/open an image from the selected source, and bring up an OpenCV window containing this window. As requested, draw boxes over the desired fitting area of the drop, and a section of the needle that is representative and clear from contamination/aberrations. After each selection, press either the "enter" or "space" key.

The automated fitting routine will then commence. A file is created with the specified name and a date-time stamp containing the fitted data.


# Version 2 changes

- Support for 3 new measurement modes has been added:
  - Sessile drop
  - Contact angle (free bubble on surface)
  - Contact angle (bubble on surface with needle present)

- Constant volume mode:
  - Allows for long term measurements of pendant droplets by compensating for
    evaporation by making small adjustments to drop volume
  - Supports [PumpSystemsInc.](http://www.syringepump.com/) syringe pumps
    (tested with NE-1000 model but other models should work)

- Genearal UI and performance tweaks


# Costant volume mode

Version 2 of OpenDrop adds support for
[PumpSystemsInc.](http://www.syringepump.com/) syringe pumps which can be
controlled via a serial interface.

Volume control mode compensates for changes in drop volume caused by evaporation
by making fine adjustments to the volume of drop via syringe pump.

**NB:** Constant volume mode is only available in pendant drop mode at the
present time.

To enable constant volume mode, check the "Constant volume" checkbox at the
bottom of the pendant drop window. Input the inner diameter of the syringe you
are using in your syringe pump, as well as the volume change threshold. Volume
changes (relative to the initial drop volume) smaller than this threshold will
not be compensated for.

Finally, select a device from the "Serial device" drop down menu. If you have
yet to plug your syringe pump into your computer, plug it in and then click the
"Update device list" button to repopulate the dropdown menu list. The "Test"
button will attempt to connect to your syringe pump and read the value in the
volume accumulator.

If the test fails, ensure your serial cable is not faulty and that
your syringe pump is switched on. Also make sure you are selecting the correct
serial device if you have multiple serial devices connected to your computer.

# Appendix A

## Preparing Ubuntu 14.04 for OpenDrop.

The following commands typed into the terminal will prepare an installation of Ubuntu 14.04.01 for OpenDrop, installing all required libraries and fixing dependencies. An unresolvable conflict (that may have since been corrected) was encountered when trying this process with 14.04.02.

**NB:** On newer versions of of Ubuntu, some packages listed below may not
longer be available for download. This is fine since those packages are not used
by newer version of OpenCV. If this is the case, the latest version of
OpenCV 2 should be installed, rather than 2.4.9. See
[here](https://opencv.org/releases.html) for the latest release of OpenCV.

```
sudo apt-get update
sudo apt-get upgrade
sudo apt-get install build-essential libgtk2.0-dev libjpeg-dev libtiff4-dev libjasper-dev libopenexr-dev cmake python-dev python-numpy python-tk libtbb-dev libeigen3-dev yasm libfaac-dev libopencore-amrnb-dev libopencore-amrwb-dev libtheora-dev libvorbis-dev libxvidcore-dev libx264-dev libqt4-dev libqt4-opengl-dev sphinx-common texlive-latex-extra libv4l-dev libdc1394-22-dev libavcodec-dev libavformat-dev libswscale-dev default-jdk ant libvtk5-qt4-dev python-pil.imagetk
sudo apt-get install python-scipy
sudo apt-get install python-matplotlib
cd ~
wget http://sourceforge.net/projects/opencvlibrary/files/opencv-unix/2.4.9/opencv-2.4.9.zip
unzip opencv-2.4.9.zip
cd opencv-2.4.9
mkdir build
cd build
cmake -D WITH_TBB=ON -D BUILD_NEW_PYTHON_SUPPORT=ON -D WITH_V4L=ON -D INSTALL_C_EXAMPLES=ON -D INSTALL_PYTHON_EXAMPLES=ON -D BUILD_EXAMPLES=ON -D WITH_QT=ON -D WITH_OPENGL=ON -D WITH_VTK=ON ..
make
sudo make install
```

After the installation has finished, add the line `/usr/local/lib` to your
`opencv.conf` and then run ldconfig:

```
sudo gedit /etc/ld.so.conf.d/opencv.conf
sudo ldconfig
```

Finally, add the lines
```
PKG_CONFIG_PATH=$PKG_CONFIG_PATH:/usr/local/lib/pkgconfig
export PKG_CONFIG_PATH
```
to your `.bashrc` or equivalent bash config file, then restart your console or
source your `.bashrc` so the changes take effect.


# Appendix B

## Upgrading from OpenDrop v1 to OpenDrop v2

The only package you need to install should be python-pil.imagetk:

```
sudo apt-get install python-pil.imagetk
```


# Appendix C

## Preparing Windows for OpenDrop.

- Download the free Anaconda Python distribution from [here](http://continuum.io/downloads), and install (tested and works with Anaconda 64-bit Python 2.7 Graphical Installer).
- Download the latest OpenCV release from [here](http://sourceforge.net/projects/opencvlibrary/files/opencv-win/) and double-click to extract it (tested and works with opencv-3.0.0-rc1.exe). The folder opencv will be created in the folder you extract to.
- Go to the opencv/build/python/2.7/x64 folder (x86 for 32-bit), and then copy cv2.pyd to the C:/Python27/lib/site-packages/ folder. If this doesn't work, or if this folder doesn't exist, copy cv2.pyd to the C:/Anaconda/Lib/site-packages/ folder.
- Now open the OpenDrop folder, and double-click on "run.bat". If everything has installed correctly, OpenDrop should start.

If you have any problems, find alternative solutions, or manage to install successfully on other Windows versions please let us know.


# Appendix D

## Preparing Mac OSX for OpenDrop.

Coming very soon!!


# Appendix E

## Installing and preparing FlyCap2 software and libraries for using Point Grey cameras on Ubuntu 14.04:

Download the prerequisite libraries:
```
sudo apt-get install glade
sudo apt-get install libraw1394-11 libgtk2.0-0 libgtkmm-2.4-dev libglademm-2.4-dev libgtkglextmm-x11-1.2-dev libusb-1.0-0
```

Download the latest FlyCapture2 Viewer software from the software section on
[this](https://www.ptgrey.com/support/downloads) website (login required).

**NB:** tested using 2.7.3.13

Unpack the FlyCapture2 Viewer zip and navigate to the directory and run:

```
sh install_flycapture.sh
```

To make the FCGrab script, copy the FlyCapture_building directory to somewhere
convenient and then build the script:

```
cd src/FCGrab
make
```
