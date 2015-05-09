#!/usr/bin/env python
#coding=utf-8
from __future__ import print_function
# from classes import ExperimentalDrop
# from subprocess import call
# import numpy as np
import cv2
# import time
# import datetime
# from Tkinter import *
# import tkFileDialog
import sys
# import os

MAX_IMAGE_TO_SCREEN_RATIO = 0.8

def set_regions(experimental_drop, experimental_setup):
    # select the drop and needle regions in the image
    screen_size = experimental_setup.screen_resolution
    image_size = experimental_drop.image.shape
    scale = set_scale(image_size, screen_size)
    screen_position = set_screen_position(screen_size)
    experimental_setup.drop_region = user_ROI(experimental_drop.image, 'Select drop region', scale, screen_position)
    experimental_setup.needle_region = user_ROI(experimental_drop.image, 'Select needle region', scale, screen_position)

def set_scale(image_size, screen_size):
    x_ratio = image_size[1]/float(screen_size[0])
    y_ratio = image_size[0]/float(screen_size[1])
    max_ratio = max(x_ratio, y_ratio)
    scale = 1
    if max_ratio > MAX_IMAGE_TO_SCREEN_RATIO: 
        scale = MAX_IMAGE_TO_SCREEN_RATIO / max_ratio
    return scale

def set_screen_position(screen_size):
    prec_free_space = 0.5 * (1 - MAX_IMAGE_TO_SCREEN_RATIO) # percentage room free
    x_position = int(prec_free_space * screen_size[0]) 
    y_position = int(0.5 * prec_free_space * screen_size[1]) # 0.5 moves window a little bit higher
    return [x_position, y_position]


def user_ROI(raw_image, title,  scale, screen_position): #, line_colour=(0, 0, 255), line_thickness=2):
    global drawing
    global ix, iy
    global fx, fy
    global image_TEMP
    global img
    # raw_image = raw_image2
    # raw_image = np.flipud(cv2.cvtColor(raw_image2,cv2.COLOR_GRAY2BGR))
    # raw_image = np.flipud(raw_image2)
    drawing = False # true if mouse is pressed
    ix,iy = -1,-1
    fx,fy = -1,-1

    

    cv2.namedWindow(title, cv2.WINDOW_AUTOSIZE)
    cv2.moveWindow(title, screen_position[0], screen_position[1])
    cv2.setMouseCallback(title, draw_rectangle)

    image_TEMP = cv2.resize(raw_image, (0,0), fx=scale, fy=scale)

    img = image_TEMP.copy()

    while(1):
        cv2.imshow(title,img)
        k = cv2.waitKey(1) & 0xFF 
        if k != 255:
            if (k == 13) or (k == 32):
                # either 'return' or 'space' pressed
                # break
                if ((fx - ix) * (fy - iy)) != 0: # ensure there is an enclosed region
                    break
            if (k == 27):
                # 'esc'
                kill()

    cv2.destroyAllWindows()
    min_x = min(ix, fx) / scale
    max_x = max(ix, fx) / scale
    min_y = min(iy, fy) / scale
    max_y = max(iy, fy) / scale
    return [(min_x, min_y), (max_x, max_y)]

# mouse callback function
def draw_rectangle(event,x,y,flags,param):
    global ix,iy,drawing
    global fx, fy
    global image_TEMP
    global img

    if event == cv2.EVENT_LBUTTONDOWN:
        img = image_TEMP.copy()
        drawing = True
        ix,iy = x,y

    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing == True:
            img = image_TEMP.copy()
            cv2.rectangle(img,(ix,iy),(x,y), (0, 0, 255), 2)# line_colour,line_thickness)

    elif event == cv2.EVENT_LBUTTONUP:
        img = image_TEMP.copy()
        drawing = False
        fx, fy = x, y
        cv2.rectangle(img,(ix,iy),(fx, fy), (0, 255, 0), 2)# #line_colour,line_thickness)

def kill():
    sys.exit()