#!/usr/bin/env python
#coding=utf-8
from __future__ import print_function
import subprocess
import cv2
import time
import datetime
import timeit
import os
import numpy as np

IMAGE_FLAG = 1 # 1 returns three channels (BGR), 0 returns gray


def get_image(experimental_drop, experimental_setup, frame_number):
    import_from_source(experimental_drop, experimental_setup, frame_number)
    # experimental_drop.image = np.flipud(cv2.imread('drop.png', 1))
    # experimental_drop.time = timeit.default_timer()
    if frame_number == 0:
        experimental_setup.time_string = datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")
        if experimental_setup.create_folder_boole:
            filename_less_extension = experimental_setup.filename[:-4] # trim off image extension
            print(filename_less_extension)
            new_directory = os.path.join(experimental_setup.directory_string, filename_less_extension + "_" + experimental_setup.time_string)
            print(new_directory)
            os.makedirs(new_directory)
            experimental_setup.directory_string = new_directory

    #if (frame_number >= 0) and (experimental_setup.save_images_boole):
    #    save_image(experimental_drop, experimental_setup, frame_number)

def save_image(experimental_drop, experimental_setup, frame_number):
    filename_temp = os.path.join(experimental_setup.directory_string, experimental_setup.filename) # gets the filename for the file to be saved
    time_string = experimental_setup.time_string # imports the time_string from the initial experiment
    filename = filename_temp[:-4] + '_' + time_string + '_' + str(frame_number).zfill(3) + filename_temp[-4:]
    cv2.imwrite(filename, experimental_drop.image)

# this routine imports the raw drop image based on user input image source
# image_source = 0 : Flea3
# image_source = 1 : USB camera
# image_source = 2 : image on computer
def import_from_source(experimental_drop, experimental_setup, frame_number):
    image_source = experimental_setup.image_source
    print(image_source)
    # from Flea3 camera
    if image_source == "Flea3":
        image_from_Flea3(experimental_drop)
    # from USB camera
    elif image_source == "USB camera":
        image_from_camera(experimental_drop)
    # from specified file
    elif image_source == "Local images":
        image_from_harddrive(experimental_drop, experimental_setup, frame_number)
    # else the value of img_src is incorrect
    else:
        ValueError("Incorrect value for image_source")
    # experimental_drop.time = datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")
    experimental_drop.time = timeit.default_timer()
    # experimental_drop.image = np.flipud(cv2.imread(experimental_drop.filename, IMAGE_FLAG))


def image_from_Flea3(experimental_drop):
    subprocess.call(["./FCGrab"])
    temp_filename = 'FCG.pgm'
    experimental_drop.image = cv2.imread(temp_filename, IMAGE_FLAG)
    #os.remove(temp_filename)
    # experimental_drop.filename

def image_from_harddrive(experimental_drop, experimental_setup, frame_number):
    import_filename = get_import_filename(experimental_setup, frame_number)
    experimental_drop.image = cv2.imread(import_filename, IMAGE_FLAG)

def get_import_filename(experimental_setup, frame_number):
    return experimental_setup.import_files[frame_number*(frame_number>0)] # handles initialisation frame = -1

# Captures a single image from the camera and returns it in IplImage format
def image_from_camera(experimental_drop):
    grabanimage()
    temp_filename = 'USBtemp.png'
    experimental_drop.image = cv2.imread(temp_filename, IMAGE_FLAG)

def grabanimage():
    camera_port = 0
    ramp_frames = 40
    camera = cv2.VideoCapture(camera_port)

    def get_image():
        retval, im = camera.read()
        return im

    for i in range(ramp_frames):
        temp = get_image()
    print("Taking image...")
# Take the actual image we want to keep
    camera_capture = get_image()
    file = "USBtemp.png"
# A nice feature of the imwrite method is that it will automatically choose the
# correct format based on the file extension you provide. Convenient!
    cv2.imwrite(file, camera_capture)
