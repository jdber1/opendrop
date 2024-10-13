#!/usr/bin/env python
#coding=utf-8
from __future__ import print_function
# from classes import ExperimentalDrop
# from subprocess import call
# import numpy as np
import cv2
import numpy as np
import matplotlib.pyplot as plt
# import time
# import datetime
# from Tkinter import *
# import tkFileDialog
import sys
from scipy import optimize # DS 7/6/21 - for least squares fit
import tensorflow as tf # DS 9/6/21 - for loading ML model

from .preprocessing import prepare_hydrophobic, tilt_correction

# import os

MAX_IMAGE_TO_SCREEN_RATIO = 0.8

def set_drop_region(experimental_drop, experimental_setup):
    # select the drop and needle regions in the image
    screen_size = experimental_setup.screen_resolution
    image_size = experimental_drop.image.shape
    scale = set_scale(image_size, screen_size)
    screen_position = set_screen_position(screen_size)
    if experimental_setup.drop_ID_method == "Automated":
        from .preprocessing import auto_crop
        experimental_drop.cropped_image, (left,right,top,bottom) = auto_crop(experimental_drop.image)

        if 1: #show found drop
            plt.title('original image')
            plt.imshow(experimental_drop.image)
            plt.show()
            plt.close()

            plt.title('cropped image')
            plt.imshow(experimental_drop.cropped_image)
            plt.show()
            plt.close()
        experimental_setup.drop_region = [(left, top),(right,bottom)]
    elif experimental_setup.drop_ID_method == "User-selected":
        experimental_setup.drop_region = user_ROI(experimental_drop.image, 'Select drop region', scale, screen_position)
        experimental_drop.cropped_image = image_crop(experimental_drop.image, experimental_setup.drop_region)
 #   experimental_setup.needle_region = user_line(experimental_drop.image, 'Select needle region', scale, screen_position)

def image_crop(image, points):
    # return image[min(y):max(y), min(x),max(x)]
    return image[int(points[0][1]):int(points[1][1]), int(points[0][0]):int(points[1][0])]

def set_surface_line(experimental_drop, experimental_setup):
    if experimental_setup.baseline_method == "Automated":
        experimental_drop.drop_contour, experimental_drop.contact_points = prepare_hydrophobic(experimental_drop.contour)
    elif experimental_setup.baseline_method == "User-selected":
        user_line(experimental_drop, experimental_setup)


def correct_tilt(experimental_drop, experimental_setup):
    if experimental_setup.baseline_method == "Automated":
        experimental_drop.cropped_image = tilt_correction(experimental_drop.cropped_image, experimental_drop.contact_points)

    #gets tricky where the baseline is manually set because under the current workflow users would
    # be required to re-input their baseline until it's flat - when the baseline should be flat
    # and known once it's set and corrected for
    elif experimental_setup.baseline_method == "User-selected":
        rotated_img_crop = tilt_correction(img, experimental_drop.contact_points, user_set_baseline=True)

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
    #scale =1
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

def user_line(experimental_drop, experimental_setup):
    #scale = set_scale(experimental_drop.image.shape, experimental_setup.screen_resolution)
    screen_position = set_screen_position(experimental_setup.screen_resolution)
    raw_image = experimental_drop.cropped_image
    drop_data = experimental_drop.contour.astype(float)
    CPs = experimental_drop.contact_points
    title = 'Define surface line'
    #line = experimental_drop.surface_data # not set yet
    region = experimental_setup.drop_region

    global drawing
    global ix, iy
    global fx, fy
    global image_TEMP
    global img

    DRAW_TANGENT_LINE_WHILE_SETTING_BASELINE = True
    TEMP = False
    baseline_def_method = 'use user-inputted points'

    # raw_image = raw_image2
    # raw_image = np.flipud(cv2.cvtColor(raw_image2,cv2.COLOR_GRAY2BGR))
    # raw_image = np.flipud(raw_image2)
    drawing = True # true if mouse is pressed
    ix,iy = -1,-1
    fx,fy = -1,-1

    region = np.floor(region)
    # print(region)

    # print(region[0,0])
    # print(region[1,0])
    # print(region[0,1])
    # print(region[1,1])

    #    cv2.setMouseCallback(title, draw_line)

    scale = 1
    if TEMP:
        image_TEMP = cv2.resize(raw_image[int(region[0,1]):int(region[1,1]),int(region[0,0]):int(region[1,0])], (0,0), fx=scale, fy=scale)
    else:
        image_TEMP = raw_image.copy()
    img = image_TEMP.copy()

    # set surface line starting estimate
    N = np.shape(drop_data)[0]
    A = 1 #50 # maybe lower this?
    xx = np.concatenate((drop_data[0:A,0],drop_data[N-A:N+1,0]))
    yy = np.concatenate((drop_data[0:A,1],drop_data[N-A:N+1,1]))
    coefficients = np.polyfit(xx, yy, 1)
    line = np.poly1d(coefficients)

    xx = np.array([0,img.shape[1]])
    yy = line(xx) #gives a starting guess for the line position

    ix0,fx0 = xx.astype(int)
    iy0,fy0 = yy.astype(int)

    ix,fx = ix0,fx0
    iy,fy = iy0,fy0

    cv2.namedWindow(title, cv2.WINDOW_AUTOSIZE)
    cv2.moveWindow(title, screen_position[0], screen_position[1])

    if DRAW_TANGENT_LINE_WHILE_SETTING_BASELINE: #so that things can be drawn over the image which surface line is changed
        conans = {}
        if 0:
            for i,n in enumerate(drop_data):
                if n[0]==CPs[0][0] and int(n[1])==int(CPs[0][1]):
                    start_index = i
                if int(n[0])==int(CPs[1][0]) and int(n[1])==int(CPs[1][1]):
                    end_index = i
            auto_drop = drop_data.copy()[start_index:end_index]
        else:
            auto_drop = drop_data

    while(1):
        cv2.imshow(title,img)
        #cv2.circle(img,(200,200),5,(255,255,0),2)
        cv2.line(img,(ix,iy),(fx,fy), (0, 255, 0), 2)# #line_colour,line_thickness)
        #Plot pixels above line
        #cv2.waitKey(0)
        v1 = (ix-fx,iy-fy) #(1,coefficients[1])   # Vector 1

        #print(np.shape(drop_data))
        #print(drop_data)

        #drop_data_list = np.ndarray.tolist(drop_data)
        #start = sorted(drop_data_list, key=lambda x: (x[1]))[-1]
        #sorted_drop_data_list = optimized_path(drop_data_list,start)
        #drop_data = np.array(sorted_drop_data_list)
        #print(type(drop_data))

        if 1:
            drop = []
            for i in drop_data:
                cx,cy = i
                v2 = (cx-ix, cy-iy)   # Vector 1
                xp = v1[0]*v2[1] - v1[1]*v2[0]  # Cross product
                if xp > 0:
                    drop.append([cx,cy])
                    cv2.circle(img,(int(cx),int(cy)),2,(255,255,255),1)
        else:
            drop = []
            for i in drop_data:
                cx,cy = i
                #if contour point y value less than line y value
                if cy < line(cx):
                    drop.append([cx,cy])
                    cv2.circle(img,(int(cx),int(cy)),2,(255,255,255),1)


        drop = np.asarray(drop).astype(float) #drop is the contour above the user-inputted line

        if 0:
            plt.imshow(img)
            plt.title('check contour after being cut by baseline')
            plt.plot(drop[:,0],drop[:,1])
            plt.show()
            plt.close()

        experimental_drop.drop_contour = drop
        CPs = {0: drop[0], 1:drop[-1]}
        experimental_drop.contact_points = CPs

        if DRAW_TANGENT_LINE_WHILE_SETTING_BASELINE:
            if experimental_setup.tangent_boole == True or experimental_setup.second_deg_polynomial_boole == True or experimental_setup.circle_boole == True or experimental_setup.ellipse_boole == True:
                from .fits import perform_fits
                perform_fits(experimental_drop, tangent=experimental_setup.tangent_boole, polynomial=experimental_setup.second_deg_polynomial_boole, circle=experimental_setup.circle_boole,ellipse=experimental_setup.ellipse_boole)
            if experimental_setup.tangent_boole == True:
                tangent_lines = tuple(experimental_drop.contact_angles['tangent fit']['tangent lines'])
                cv2.line(img, (int(tangent_lines[0][0][0]),int(tangent_lines[0][0][1])),(int(tangent_lines[0][1][0]),int(tangent_lines[0][1][1])), (0, 0, 255), 2)
                cv2.line(img, (int(tangent_lines[1][0][0]),int(tangent_lines[1][0][1])),(int(tangent_lines[1][1][0]),int(tangent_lines[1][1][1])),(0, 0, 255), 2)
            if experimental_setup.second_deg_polynomial_boole == True and experimental_setup.tangent_boole == False:
                tangent_lines = tuple(experimental_drop.contact_angles['polynomial fit']['tangent lines'])
                cv2.line(img, tangent_lines[0][0],tangent_lines[0][1], (0, 0, 255), 2)
                cv2.line(img, tangent_lines[1][0],tangent_lines[1][1], (0, 0, 255), 2)
            if experimental_setup.circle_boole == True:
                xc,yc = experimental_drop.contact_angles['circle fit']['circle center']
                r = experimental_drop.contact_angles['circle fit']['circle radius']
                cv2.circle(img,(int(xc),int(yc)),int(r),(255,150,0),1)
            if experimental_setup.ellipse_boole == True:
                center = experimental_drop.contact_angles['ellipse fit']['ellipse center']
                axes = experimental_drop.contact_angles['ellipse fit']['ellipse a and b']
                phi = experimental_drop.contact_angles['ellipse fit']['ellipse rotation']
                cv2.ellipse(img, (int(center[0]),int(center[1])), (int(axes[0]),int(axes[1])), phi, 0, 360, (0, 88, 255), 1)

        k = cv2.waitKey(1) & 0xFF
        #print(k)
        if k != 255:

            if (k == 13) or (k == 32):
                # either 'return' or 'space' pressed
                # break
                if ((fx - ix) * (fy - iy)) != 0: # ensure there is an enclosed region
                    break
                else: # something weird happening here, insert work around
                    print('something is not right...')
                    print(fx)
                    print(ix)
                    print(fy)
                    print(iy)
                    print(((fx - ix) * (fy - iy)))
                    break

            if (k == 27):
                # 'esc'
                kill()
            if (k==-1):
                continue
            if (k == 0): #up key (down on image)
                fy = fy+1
                iy = iy+1

                if TEMP:
                    image_TEMP = cv2.resize(raw_image[int(region[0,1]):int(region[1,1]),int(region[0,0]):int(region[1,0])], (0,0), fx=scale, fy=scale)
                else:
                    image_TEMP = raw_image.copy()
                img = image_TEMP.copy()
                cv2.line(img,(ix,iy),(fx, fy), (0, 255, 0), 2)# #line_colour,line_thickness)    cv2.line
            if (k == 1): #down key (up on image)
                fy = fy-1
                iy = iy-1

                if TEMP:
                    image_TEMP = cv2.resize(raw_image[int(region[0,1]):int(region[1,1]),int(region[0,0]):int(region[1,0])], (0,0), fx=scale, fy=scale)
                else:
                    image_TEMP = raw_image.copy()
                img = image_TEMP.copy()
                cv2.line(img,(ix,iy),(fx, fy), (0, 255, 0), 2)# #line_colour,line_thickness)    cv2.line


            if (k == 111): #"o" key
                if 1:
                    fx,fy = fx0,fy0
                    ix,iy = ix0,iy0

                    if TEMP:
                        image_TEMP = cv2.resize(raw_image[int(region[0,1]):int(region[1,1]),int(region[0,0]):int(region[1,0])], (0,0), fx=scale, fy=scale)
                    else:
                        image_TEMP = raw_image.copy()
                    img = image_TEMP.copy()
                    cv2.line(img,(ix,iy),(fx, fy), (0, 255, 0), 2)# #line_colour,line_thickness)    cv2.line
                else:
                    if TEMP:
                        image_TEMP = cv2.resize(raw_image[int(region[0,1]):int(region[1,1]),int(region[0,0]):int(region[1,0])], (0,0), fx=scale, fy=scale)
                    else:
                        image_TEMP = raw_image.copy()
                    img = image_TEMP.copy()
                    #cv2.line(img,())


            if (k == 2) or (k == 3): #83: right key (Clockwise)
                x0 = np.array([ix,iy])
                x1 = np.array([fx,fy])
                xc = 0.5*(x0+x1)
                theta = 0.1/180*np.pi
                if (k == 2):  #left key
                    theta = -theta

                rotation = np.zeros((2,2))
                rotation[0,0] = np.cos(theta)
                rotation[0,1] = -np.sin(theta)
                rotation[1,0] = np.sin(theta)
                rotation[1,1] = np.cos(theta)

                x0r = np.dot(rotation,(x0-xc).T)+xc
                x1r = np.dot(rotation,(x1-xc).T)+xc

                ix,iy = x0r.astype(int)
                fx,fy = x1r.astype(int)

                if TEMP:
                    image_TEMP = cv2.resize(raw_image[int(region[0,1]):int(region[1,1]),int(region[0,0]):int(region[1,0])], (0,0), fx=scale, fy=scale)
                else:
                    image_TEMP = raw_image.copy()
                img = image_TEMP.copy()
                cv2.line(img,(ix,iy),(fx, fy), (0, 255, 0), 2)# #line_colour,line_thickness)    cv2.line

            if (k == 112): #'p' key
                #print(contact_angle1,contact_angle2)
                for key in conans.keys():
                    print(key,': ',conans[key])
                print()
                #print(conans)
                #print(m1,m2)

            if (k == -1):
                continue
#            else:
#                print(k)


    cv2.destroyAllWindows()
    min_x = min(ix, fx) / scale
    max_x = max(ix, fx) / scale
    min_y = min(iy, fy) / scale
    max_y = max(iy, fy) / scale

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

# mouse callback function
def draw_line(event,x,y,flags,param):
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
            cv2.line(img,(ix,iy),(x,y), (0, 0, 255), 2)# line_colour,line_thickness)

    elif event == cv2.EVENT_LBUTTONUP:
        img = image_TEMP.copy()
        drawing = False
        fx, fy = x, y
        cv2.line(img,(ix,iy),(fx, fy), (0, 255, 0), 2)# #line_colour,line_thickness)

def kill():
    sys.exit()

def distance(P1, P2):
    """This function computes the distance between 2 points defined by
    P1 = (x1,y1) and P2 = (x2,y2) """
    return ((P1[0] - P2[0])**2 + (P1[1] - P2[1])**2) ** 0.5

def optimized_path(coords, start=None):
    """This function finds the nearest point to a point
    coords should be a list in this format coords = [ [x1, y1], [x2, y2] , ...]
    https://stackoverflow.com/questions/45829155/sort-points-in-order-to-have-a-continuous-curve-using-python"""
    if isinstance(coords,list) == False:
        coords = coords.tolist()
    if 0 :
        if isinstance(start,list) == False:
            try:
                start = start.tolist()
            except:
                start = list(start)
    if start is None:
        start = coords[0]
    pass_by = coords
    path = [start]
    pass_by.remove(start)
    while pass_by:
        nearest = min(pass_by, key=lambda x: distance(path[-1], x))
        path.append(nearest)
        pass_by.remove(nearest)
    path = np.array(path)
    return path



def intersection(center, radius, p1, p2):

    """ find the two points where a secant intersects a circle """

    dx, dy = p2[0] - p1[0], p2[1] - p1[1]

    a = dx**2 + dy**2
    b = 2 * (dx * (p1[0] - center[0]) + dy * (p1[1] - center[1]))
    c = (p1[0] - center[0])**2 + (p1[1] - center[1])**2 - radius**2

    discriminant = b**2 - 4 * a * c
    assert (discriminant > 0), 'Not a secant!'

    t1 = (-b + discriminant**0.5) / (2 * a)
    t2 = (-b - discriminant**0.5) / (2 * a)

    return (dx * t1 + p1[0], dy * t1 + p1[1]), (dx * t2 + p1[0], dy * t2 + p1[1])

def ML_prepare_hydrophobic(coords_in):
    coords = coords_in
    coords[:,1] = - coords[:,1] # flip
    #print('length of coords: ',len(coords))

    # isolate the top of the contour so excess surface can be deleted
    percent = 0.1
    bottom = []
    top = [] # will need this later
    div_line_value = min(coords[:,[1]]) + (max(coords[:,[1]]) - min(coords[:,[1]]))*percent
    for n in coords:
        if n[1] < div_line_value:
            bottom.append(n)
        else:
            top.append(n)

    bottom = np.array(bottom)
    top = np.array(top)

    del_indexes = []
    for index,coord in enumerate(coords):
        if coord[0]>max(top[:,0]) or coord[0]<min(top[:,0]):
            del_indexes.append(index)
    #halfdrop = np.delete(halfdrop,del_indexes)
    coords = np.delete(coords,del_indexes,axis=0)

    if 0:
        plt.title('isolated coords, length: '+str(len(coords)))
        plt.plot(coords[:,0],coords[:,1])
        plt.show()
        plt.close()



    # find the apex of the drop and split the contour into left and right sides

    xtop,ytop = top[:,0],top[:,1] # isolate top 90% of drop

    xapex = (max(xtop) + min(xtop))/2
    #yapex = max(ytop)
    #coords[:,1] = -coords[:,1]

    l_drop = []
    r_drop = []
    for n in coords:
        if n[0] < xapex:
            l_drop.append(n)
        if n[0] > xapex:
            r_drop.append(n)
    l_drop = np.array(l_drop)
    r_drop = np.array(r_drop)

    #print('length of left drop is: ',len(l_drop))
    #print('length of right drop is: ', len(r_drop))

    # transpose both half drops so that they both face right and the apex of both is at 0,0
    #r_drop[:,[0]] = r_drop[:,[0]] - min(r_drop[:,[0]])
    #l_drop[:,[0]] = -l_drop[:,[0]] + max(l_drop[:,[0]])
    r_drop[:,[0]] = r_drop[:,[0]] - xapex
    l_drop[:,[0]] = -l_drop[:,[0]] + xapex

    counter = 0
    CV_contours = {}

    for halfdrop in [l_drop,r_drop]:
        if halfdrop[0,1]<halfdrop[-1,1]:
            halfdrop = halfdrop[::-1]

        X = halfdrop[:,0]
        Z = halfdrop[:,1]

        lowest = min(Z)
        Z = Z+abs(lowest)

        X = X/max(Z)
        Z = Z/max(Z)

        # zero padd contours to
        coordinates = []
        input_len = 1100
        len_cont = len(X)

        #if len(X) > global_max_len:
        #    global_max_len = len(X)

        if len(X)>input_len:
            print(len(X))
            raise Exception("Contour of length "+str(len(X))+" is too long for the designated output dimensionality of ("+str(input_len)+",2)")

        for i in range(input_len):
            if i < len(X):
                a = X[i]
                b = Z[i]
                coord = [a,b]
                coordinates.append(coord)
            else:
                coordinates.append([0,0])
        if 0:
            jet= plt.get_cmap('jet')
            colors = iter(jet(np.linspace(0,1,len(coordinates))))
            for k in coordinates:
                plt.plot(k[0],k[1], 'o',color=next(colors))
            plt.title('Halfdrop')
            plt.show()
            plt.close()
        #key = image.split('/')[-1].split('_')[-1][:-4]
        key = counter
        CV_contours[key]= np.array(coordinates)

        counter += 1

    pred_ds = np.zeros((2,input_len,2))
    for counter in [0,1]:
        pred_ds[counter] = CV_contours[counter]

    return pred_ds
