#!/usr/bin/env python
#coding=utf-8
from __future__ import print_function
import numpy as np
import cv2
import matplotlib.pyplot as plt
from sklearn.cluster import OPTICS # DS 7/6/21 - for clustering algorithm
# import time
# import datetime
from modules.preprocessing.preprocessing import extract_edges_CV

BLUR_SIZE = 3
VERSION_CV2 = cv2.__version__

def extract_drop_profile(raw_experiment, user_inputs):
    if user_inputs.threshold_method == "User-selected":
        # profile_edges = detect_edges(raw_experiment.cropped_image, raw_experiment, user_inputs.drop_region)
        # profile, raw_experiment.ret = detect_edges(raw_experiment.cropped_image, raw_experiment, user_inputs.drop_region)
        raw_experiment.contour, raw_experiment.ret = detect_edges(raw_experiment.cropped_image, raw_experiment, user_inputs.drop_region, 1, user_inputs.threshold_val)

        if 1:
            plt.imshow(raw_experiment.cropped_image)
            plt.plot(raw_experiment.contour[:,0],raw_experiment.contour[:,1],'r,')
            plt.title('Extracted drop profile\nTheshold value of : '+str(raw_experiment.ret))
            plt.axis('equal')
            plt.show()
            plt.close()

    elif user_inputs.threshold_method == "Automated":
        if raw_experiment.ret  == None:
            raw_experiment.contour, raw_experiment.ret = extract_edges_CV(raw_experiment.cropped_image, return_thresholed_value=True)

            if user_inputs.show_popup == 1:
                plt.imshow(raw_experiment.cropped_image)
                plt.plot(raw_experiment.contour[:,0],raw_experiment.contour[:,1],'r,')
                plt.title('Extracted drop profile\nTheshold value of : '+str(raw_experiment.ret))
                plt.axis('equal')
                plt.show()
                plt.close()
        else:
            # if a threshold value has been selected then use this
            raw_experiment.contour = extract_edges_CV(raw_experiment.cropped_image, threshold_val=raw_experiment.ret, return_thresholed_value=False)



    #needle_crop = image_crop(raw_experiment.image, user_inputs.needle_region)
    #raw_experiment.needle_data, ret = detect_edges(needle_crop, raw_experiment, user_inputs.needle_region, raw_experiment.ret, 2)

    # # detect needle edges
    # needle_crop = image_crop(raw_experiment.image, user_inputs.needle_region)
    # raw_experiment.needle_data = detect_edges(needle_crop, user_inputs.needle_region)

def image_crop(image, points): # loaded in conan.py
    # return image[min(y):max(y), min(x),max(x)]
    return image[int(points[0][1]):int(points[1][1]), int(points[0][0]):int(points[1][0])]

def detect_edges(image, raw_experiment, points, n_contours, threshValue):

    if len(image.shape) != 2:
        image = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)

    if 1:
        blur = cv2.GaussianBlur(image,(BLUR_SIZE,BLUR_SIZE),0) # apply Gaussian blur to drop edge

    #    if ret == -1:
    ret, thresh = cv2.threshold(blur,threshValue,255,cv2.THRESH_BINARY)#+cv2.THRESH_OTSU) # calculate thresholding
    # else:
    #     ret, thresh = cv2.threshold(blur,ret,255,cv2.THRESH_BINARY) # calculate thresholding
    # these values seem to agree with
    # - http://www.academypublisher.com/proc/isip09/papers/isip09p109.pdf
    # - http://stackoverflow.com/questions/4292249/automatic-calculation-of-low-and-high-thresholds-for-the-canny-operation-in-open
    # edges = cv2.Canny(thresh,0.5*ret,ret) # detect edges using Canny edge detection

    # error in PDT code - shouldn't threshold before Canny - otherwise Canny is useless
    #edges = cv2.Canny(blur,0.5*ret,ret) # detect edges using Canny edge detection

    contours, hierarchy = cv2.findContours(thresh,cv2.RETR_TREE,cv2.CHAIN_APPROX_NONE)

    #contour_lengths = [length for length in cv2.arcLength(contours,0)] #list to hold all areas
    contour_lengths = [cv2.arcLength(contour,0) for contour in contours] #list to hold all areas

    indexed_contour_lengths = np.array(contour_lengths).argsort()[::-1]
    indexed_contours_to_return = indexed_contour_lengths[:n_contours]

    image_height = raw_experiment.image.shape[0]

    offset = [0,0]#[0, image.shape[1]]
    points = []
    for index in indexed_contours_to_return:
        current_contour = contours[index][:,0]
        for i in range(current_contour.shape[0]):
            current_contour[i,1] = current_contour[i,1]
            current_contour[i,:] = current_contour[i,:] + offset
            #points.append(current_contour[current_contour[:,1].argsort()])


    size = 0
    cropped_image_height = image.shape[0]
    cropped_image_width = image.shape[1]
    for i in range(current_contour.shape[0]): #Trim edges from contour #current_contour error
        if current_contour[i,0] != 0:
            if current_contour[i,0] != cropped_image_width-1:
                if current_contour[i,1] != 0:
                    if current_contour[i,1] != (cropped_image_height-1):
                        size = size+1
#    print(current_contour.shape[0])
#    print(size)
    contour_trimmed = np.zeros((size,2))

    index = 0
    for i in range(current_contour.shape[0]):
        if current_contour[i,0] != 0:
            if current_contour[i,0] != cropped_image_width-1:
                if current_contour[i,1] != 0:
                    if current_contour[i,1] != (cropped_image_height-1):
                        contour_trimmed[index,:] = current_contour[i,:]
                        index = index+1

    contour_x = contour_trimmed[:,0]
    contour_y = contour_trimmed[:,1]

    if 0:
        plt.axis('equal')
        plt.imshow(image)
        plt.plot(contour_x,contour_y,'rs',markerfacecolor='none')
        plt.show()
        #cv2.imshow('img',image)
        #cv2.imshow('img',thresh)
        #cv2.drawContours(image,contour_trimmed)
        #cv2.drawContours(image,contours,0,(0,255,0),10)
        #cv2.drawContours(image,contours,1,(255,255,0),10)
        #cv2.waitKey(0)

        #plt.imshow(image, origin='upper', cmap = 'gray')

    # find line between first and last contour points to estimate surface line
    if 0:
        contour_pts = contour_trimmed
        N = np.shape(contour_pts)[0]
        A = 1 #50 # maybe lower this?
        #xx = np.concatenate((contour_x[0:A],contour_x[N-A:N+1]))
        #yy = np.concatenate((contour_y[0:A],contour_y[N-A:N+1]))
        xx = np.concatenate((contour_pts[0:A,0],contour_pts[N-A:N+1,0]))
        yy = np.concatenate((contour_pts[0:A,1],contour_pts[N-A:N+1,1]))


        coefficients = np.polyfit(xx, yy, 1)
        line = np.poly1d(coefficients)
        prepared_contour, CPs = prepare_hydrophobic(contour_pts)
        return prepared_contour, ret # returns no surface line
        #return contour_pts, line, ret
    else:
        N = np.shape(contour_trimmed)[0]
        A = 1 #50 # maybe lower this?
        #xx = np.concatenate((contour_x[0:A],contour_x[N-A:N+1]))
        #yy = np.concatenate((contour_y[0:A],contour_y[N-A:N+1]))
        xx = np.concatenate((contour_trimmed[0:A,0],contour_trimmed[N-A:N+1,0]))
        yy = np.concatenate((contour_trimmed[0:A,1],contour_trimmed[N-A:N+1,1]))

        coefficients = np.polyfit(xx, yy, 1)
        line = np.poly1d(coefficients)
        return contour_trimmed.astype(float), ret
    #




    # points = largest_contour[largest_contour[:,1].argsort()]


    # # determines the largest contour.
    # # hierarchy describes parent-child relationship
    # # this routine determines the length of each contour
    # # and returns the largest
    # drop_index = 0
    # maxLength = 0.0
    # for i in range(np.max(hierarchy+1)):
    #     length = cv2.arcLength(contours[i],0)
    #     # print(i, length)
    #     if length > maxLength:
    #         maxLength = length
    #         drop_index = i


    # # the largest contour
    # largest_contour = contours[drop_index][:,0]

    # # converts the data to (x, y) data where (0, 0) is the lower-left pixel
    # image_height = raw_experiment.image.shape[0]
    # offset = [points[0][0], image_height - points[0][1]]
    # for i in range(largest_contour.shape[0]):
    #     largest_contour[i,1] = - largest_contour[i,1]
    #     largest_contour[i,:] = largest_contour[i,:] + offset
    # points = largest_contour[largest_contour[:,1].argsort()]

    # return points, ret

# def calculate_needle_diameter(raw_experiment, fitted_drop_data, tolerances):

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

from sklearn.cluster import OPTICS # for clustering algorithm

def prepare_hydrophobic(coords,xi=0.8):
    """takes an array (n,2) of coordinate points, and returns the left and right halfdrops of the contour.
    xi determines the minimum steepness on the reachability plot that constitutes a cluster boundary of the
    clustering algorithm.
    deg is the degree of the polynomial used to describe the shape of the droplet.

    This code is adapted from the prepare module, but this version differs in that it assumes that the drop
    is hydrophobic."""
    # scan for clusers to remove noise and circle from lensing effect
                ################  MAY NEED TO OPTIMIZE eps/xi TO FIND APPROPRIATE GROUPINGS  ####################
    if 0: # turn this off bc using synthetic drops without lensing effect
        input_contour = coords
        dic,dic2 = cluster_OPTICS(input_contour,xi=xi),cluster_OPTICS(input_contour,out_style='xy',xi=xi)

        #print("number of groups: ",len(list(dic.keys())))

        jet= plt.get_cmap('jet')
        colors = iter(jet(np.linspace(0,1,len(list(dic.keys())))))
        for k in dic.keys():
            plt.plot(dic2[str(k)+'x'],dic2[str(k)+'y'], 'o',color=next(colors))
        plt.title(str(len(dic.keys()))+" groups found by clustering")
        plt.show()
        plt.close()
        maxkey=max(dic, key=lambda k: len(dic[k]))

        #print('key to longest dictionary entry is: ',maxkey)

        # take the longest group
        longest = dic[maxkey]

    # flip contour so that min and max values are correct
    for coord in coords:
        coord[1] = -coord[1]

    longest = coords

    #print("first few coordinates of the longest contour: ",longest[:3])

    xlongest = []
    ylongest = []
    for i in range(len(longest)):
        xlongest.append(longest[i][0])
        ylongest.append(longest[i][1])

    #print("first few x coordinates of the longest contour: ",xlongest[:3])
    #print("first few y coordinates of the longest contour: ",ylongest[:3])


    # Find a appropriate epsilon value for cluster_OPTICS, this will remove noise in the bottom 10% of the drop
    #.   most importantly noise is reduced at contact points.

    # variables in this process are how much and what part of the top of the droplet we use to be representative of
        # the full contour, and whether we use the max(distance) between points or the average between points, or
        # a scalar value of either.

    xtop = [] # isolate top 90% of drop
    ytop = []
    percent = 0.05
    #print('Isolate the top ',100-(percent*100),'% of the contour:')
    for n,y in enumerate(ylongest):
        if y > min(ylongest) + (max(ylongest) - min(ylongest))*percent:
            xtop.append(xlongest[n])
            ytop.append(y)
    xtop = np.array(xtop)
    ytop = np.array(ytop)

    top = []
    for n,x in enumerate(xtop):
        top.append([xtop[n],ytop[n]])
    top = np.array(top)
    top_array = optimized_path(top)

    dists = [] # find the average distance between points
    for n,co in enumerate(top_array):
        if 1<n:
            a = top_array[n]
            dist = np.linalg.norm(top_array[n]-top_array[n-1])
            dists.append(dist)

    if 0:
        #print(dists)
        print()
        print('Max dist between points is: ',max(dists))
        print('Average dist between points is: ',sum(dists)/len(dists))
        print('20% over the Max dist is: ', max(dists)*1.2)
        print()
        print('Sort using cluster_OPTICS with an epsilon value of ',max(dists)*1.2)

    # how epsilon is chosen here is important
    #eps = (sum(dists)/len(dists))*2 # eps is 2 times the average distance between points
    eps = (sum(dists)/len(dists))*2.5 # eps is 2.5 times the average distance between points
    input_contour = longest
    dic,dic2 = cluster_OPTICS(input_contour,eps=eps),cluster_OPTICS(input_contour,out_style='xy',eps=eps)

    #print("number of groups: ",len(list(dic.keys())))
    if 0:
        jet= plt.get_cmap('jet')
        colors = iter(jet(np.linspace(0,1,len(list(dic.keys())))))
        for k in dic.keys():
            plt.plot(dic2[str(k)+'x'],dic2[str(k)+'y'], 'o',color=next(colors))
        plt.title('Groups found by clustering with epsilon value of '+str(eps))
        plt.show()
        plt.close()
    maxkey=max(dic, key=lambda k: len(dic[k]))
    longest = dic[maxkey]
    #print("first few coordinates of the longest contour: ",longest[:3])


    xlongest = []
    ylongest = []
    for i in range(len(longest)):
        xlongest.append(longest[i][0])
        ylongest.append(longest[i][1])

    outline = np.empty((len(xlongest),2))
    for i in range(len(xlongest)):
        outline[i,[0]]=xlongest[i]
        outline[i,[1]]=ylongest[i]


    ############################

    # find the apex of the drop and split the contour into left and right sides

    xtop = [] # isolate top 90% of drop
    ytop = []
    # percent = 0.1 # already defined
    #print('isolate the top ',100-(percent*100),'% of the contour:')
    for n,y in enumerate(ylongest):
        if y > min(ylongest) + (max(ylongest) - min(ylongest))*percent:
            xtop.append(xlongest[n])
            ytop.append(y)
    xapex = (max(xtop) + min(xtop))/2
    #print('The x value of the apex is: ',xapex)

    l_drop = []
    r_drop = []
    for n in longest:
        if n[0] < xapex:
            l_drop.append(n)
        if n[0] > xapex:
            r_drop.append(n)
    l_drop = np.array(l_drop)
    r_drop = np.array(r_drop)



    # transpose both half drops so that they both face right and the apex of both is at 0,0
    r_drop[:,[0]] = r_drop[:,[0]] - xapex
    l_drop[:,[0]] = -l_drop[:,[0]] + xapex

    if 0:
        plt.plot(r_drop[:,[0]], r_drop[:,[1]], 'b,')
        #plt.show()
        #plt.close()
        plt.plot(l_drop[:,[0]], l_drop[:,[1]], 'r,')
        #plt.gca().set_aspect('equal', adjustable='box')
        #plt.xlim([470,530])
        #plt.ylim([-188,-190])
        plt.show()
        plt.close()

    #############################

    # the drop has been split in half

    # this system has a user input which gives a rough indication of the contact point and the surface line

    # isolate the bottom 5% of the contour near the contact point

    drops = {}
    counter = 0
    crop_drop = {}
    CPs = {}
    for halfdrop in [l_drop,r_drop]:
        xhalfdrop = halfdrop[:,[0]].reshape(len(halfdrop[:,[0]]))
        yhalfdrop = halfdrop[:,[1]].reshape(len(halfdrop[:,[1]]))

        # isolate the bottom of the drop to help identify contact points (may not need to do this for all scenarios)
        bottom = []
        top = [] # will need this later
        #print('isolate the bottom ',percent*100,'% of the contour:') # percent defined above
        div_line_value = min(halfdrop[:,[1]]) + (max(halfdrop[:,[1]]) - min(halfdrop[:,[1]]))*percent
        for n in halfdrop:
            if n[1] < div_line_value:
                bottom.append(n)
            else:
                top.append(n)

        bottom = np.array(bottom)
        top = np.array(top)

        xbottom = bottom[:,[0]].reshape(len(bottom[:,[0]]))
        ybottom = bottom[:,[1]].reshape(len(bottom[:,[1]]))
        xtop = top[:,[0]].reshape(len(top[:,[0]]))
        ytop = top[:,[1]].reshape(len(top[:,[1]]))

        #print('max x value of halfdrop is: ',max(xhalfdrop))

        if 0: # plot the bottom 10% of the contour
            plt.plot(xbottom, ybottom, 'b,')
            plt.title('bottom 10% of the contour')
            #plt.xlim([130,200])
            plt.show()
            plt.close()

        #### Continue here assuming that the drop is hydrophobic ####

        xCP = min(xbottom)
        yCP = []
        for coord in halfdrop:
            if coord[0]==xCP:
                yCP.append(coord[1])
        yCP =min(yCP)
        #print('The first few coordinates of xhalfdrop are: ', xhalfdrop[:3])

        #print('The coordinates of the contact point are (',xCP,',',yCP,')')

        CPs[counter] = [xCP, yCP]
        if 1:
            # order all halfdrop points using optimized_path (very quick but occasionally makes mistakes)

            new_halfdrop = sorted(halfdrop.tolist(), key=lambda x: (-x[0],x[1]))
            new_halfdrop = optimized_path(new_halfdrop)[::-1]
            xnew_halfdrop = new_halfdrop[:,[0]].reshape(len(new_halfdrop[:,[0]]))
            ynew_halfdrop = new_halfdrop[:,[1]].reshape(len(new_halfdrop[:,[1]]))

            # remove surface line past the contact point

            xCP_index = [i for i, j in enumerate(xnew_halfdrop) if j == xCP]
            #print('xCP_index is: ',xCP_index)
            yCP_index = [i for i, j in enumerate(ynew_halfdrop) if j == yCP]
            #print('yCP_index is: ',yCP_index)

            new_halfdrop = np.zeros((len(xnew_halfdrop),2))
            for n in range(len(xnew_halfdrop)):
                new_halfdrop[n,[0]]=xnew_halfdrop[n]
                new_halfdrop[n,[1]]=ynew_halfdrop[n]
            #print('first 3 points of new_halfdrop are: ',new_halfdrop[:3])
            #print('length of new_halfdrop is: ',len(new_halfdrop))

            if xCP_index == yCP_index:
                if new_halfdrop[xCP_index[0]+1][1]>new_halfdrop[xCP_index[0]-1][1]:
                    new_halfdrop = new_halfdrop[xCP_index[0]:]
                else:
                    new_halfdrop = new_halfdrop[:xCP_index[0]+1]
            else:
                raise_error = True
                for x in xCP_index:
                    for y in yCP_index:
                        if x==y:
                            raise_error = False
                            xCP_index = [x]
                            yCP_index = [y]
                            #print('indexes of the CP are: ',xCP_index[0],', ',yCP_index[0])
                            if new_halfdrop[xCP_index[0]+1][1]>new_halfdrop[xCP_index[0]-1][1]:
                                new_halfdrop = new_halfdrop[xCP_index[0]:]
                            else:
                                new_halfdrop = new_halfdrop[:xCP_index[0]+1]
                if raise_error == True:
                    print('The index of the contact point x value is: ', new_halfdrop[xCP_index])
                    print('The index of the contact point y value is: ', new_halfdrop[yCP_index])
                    raise 'indexes of x and y values of the contact point are not the same'

        if 0:
            # order all halfdrop points using two-opt (the slower method)

            # before any ordering is done, chop off the surface line that is past the drop edge
            del_indexes = []
            for index,coord in enumerate(bottom):
                if coord[0]>max(xtop):
                    del_indexes.append(index)
                if coord[1]<yCP:
                    del_indexes.append(index)
            #halfdrop = np.delete(halfdrop,del_indexes)
            xbot = np.delete(bottom[:,0],del_indexes)
            ybot = np.delete(bottom[:,1],del_indexes)

            #bottom = np.empty((len(xbot),2))
            #for n, coord in enumerate(bottom):
            #    bottom[n,0] = xbot[n]
            #    bottom[n,1] = ybot[n]

            bottom = np.array(list(zip(xbot,ybot)))

            #print('shape of another_halfdrop is: '+ str(type(another_halfdrop)))
            print('first few points of halfdrop are: ',halfdrop[:3])
            if 0:
                colors = iter(jet(np.linspace(0,1,len(bottom))))
                for n,coord in enumerate(bottom):
                    plt.plot(bottom[n,0],bottom[n,1], 'o', color=next(colors))
                plt.title('Cropped bottom of hafldrop')
                plt.show()
                plt.close()


            # order points using traveling salesman two_opt code
            bottom = bottom[::-1] # start at the top
            print('Starting first coordinate of bottom slice of halfdrop is: ',bottom[0])
            new_bot, _ = two_opt(bottom,0.01) # increase improvement_threshold from 0.1 to 0.01
            if new_bot[0,1]<new_bot[-1,1]:
                new_bot = new_bot[::-1]
            xbot,ybot = new_bot[:,[0]],new_bot[:,[1]]

            if 0: #display
                colors = iter(jet(np.linspace(0,1,len(bottom))))
                for n,coord in enumerate(bottom):
                    plt.plot(new_bot[n,0],new_bot[n,1], 'o', color=next(colors))
                plt.title('Cropped ordered new_bot of halfdrop (starting from blue)')
                plt.show()
                plt.close()

                plt.plot(new_bot[:,0],new_bot[:,1])
                plt.title('Cropped ordered new_bot of halfdrop (line)')
                plt.show()
                plt.close()

            # order the top 90% so that the y value decreases

            print('Sorting top ',100-(percent*100),'% of the contour by y value...')
            new_top = sorted(list(top), key=lambda x: x[1], reverse=True)
            new_top = np.array(new_top)

            # remove surface by deleting points after the contact point
            xCP_indexs = [i for i, j in enumerate(xbot) if j == xCP]
            #print('xCP_index is: ',xCP_index)
            yCP_indexs = [i for i, j in enumerate(ybot) if j == yCP]
            #print('yCP_index is: ',yCP_index)

            for xCP_index in xCP_indexs:
                for yCP_index in yCP_indexs:
                    if xCP_index == yCP_index:
                        try:
                            if ybot[yCP_index+2] > ybot[yCP_index-1]:
                                new_bot = np.zeros((len(xbot[yCP_index:]),2))
                                for n in range(len(new_bot)):
                                    new_bot[n,[0]] = xbot[xCP_index+n]
                                    new_bot[n,[1]] = ybot[yCP_index+n]
                            else:
                                new_bot = np.zeros((len(xbot[:yCP_index]),2))
                                for n in range(len(new_bot)):
                                    new_bot[n,[0]] = xbot[n]
                                    new_bot[n,[1]] = ybot[n]
                        except:
                            try:
                                if ybot[yCP_index] > ybot[yCP_index-2]:
                                    new_bot = np.zeros((len(xbot[yCP_index:]),2))
                                    for n in range(len(new_bot)):
                                        new_bot[n,[0]] = xbot[xCP_index+n]
                                        new_bot[n,[1]] = ybot[yCP_index+n]
                                else:
                                    new_bot = np.zeros((len(xbot[:yCP_index]),2))
                                    for n in range(len(new_bot)):
                                        new_bot[n,[0]] = xbot[n]
                                        new_bot[n,[1]] = ybot[n]
                            except:
                                print('xCP_indexs are: ', xCP_indexs)
                                print('yCP_indexs are: ', yCP_indexs)
                                raise 'indexes of x and y values of the contact point are not the same'
            new_halfdrop = np.concatenate((new_top,new_bot))

        if 0: # order the points so that the baseline can be removed
            # before any ordering is done, chop off the surface line that is past the drop edge
            del_indexes = []
            for index,coord in enumerate(halfdrop):
                if coord[0]>max(xtop):
                    del_indexes.append(index)
            #halfdrop = np.delete(halfdrop,del_indexes)
            xhalfdrop = np.delete(xhalfdrop,del_indexes)
            yhalfdrop = np.delete(yhalfdrop,del_indexes)
            #print('shape of another_halfdrop is: '+ str(type(another_halfdrop)))
            #print('first few points of halfdrop are: ',halfdrop[:3])



            # order half contour points
            xx,yy = sort_to_line(xhalfdrop,yhalfdrop)
            add_top = False
            #print('length of halfdrop is: ', len(halfdrop))
            #print('length of xbottom is: ', len(xbottom))

            #if xx[0]<1: # then graph starts at the top
            surface_past_drop_index = []
            for n,x in enumerate(xx):
                if x>max(xtop):
                    surface_past_drop_index.append(n)
                    #xx = xx[:max(xtop)point]
            #print('Indexes of contour points past drop: ',surface_past_drop_index)


            # if the sort method will not work
            if len(xx) < len(xhalfdrop): # assumes that the error is on the surface somewhere, so uses bottom of contour
                add_top = True
                print()
                print('sort_to_line is not utilising the full contour, alternate ordering method being used')
                print('check bottom 10% of contour...')
                # this method is much slower than the above, so use as few points as possible
                bot_list = []
                for n in range(len(xbottom)):
                    if xbottom[n]<max(xtop):
                        bot_list.append([xbottom[n],ybottom[n]])
                bot_array = np.array(bot_list)
                new_order, _ = two_opt(bot_array) # 119.8 seconds for 247 points

                xbot,ybot = new_order[:,[0]],new_order[:,[1]]

                if 0:
                    plt.plot(xbot,ybot,'b-')
                    plt.title('Bottom of half drop, new order')
                    plt.show()
                    plt.close()

                xCP_index = [i for i, j in enumerate(xbot) if j == xCP]
                #print('xCP_index is: ',xCP_index)
                yCP_index = [i for i, j in enumerate(ybot) if j == yCP]
                #print('yCP_index is: ',yCP_index)

                if 0:
                    new_bot = np.zeros((len(xbot),2))
                    for n in range(len(xx)):
                        new_bot[n,[0]] = xbot[n]
                        new_bot[n,[1]] = ybot[n]
                #xbot[xCP_index[0]:]
                if xCP_index == yCP_index:
                    if ybot[yCP_index[0]+1] > ybot[yCP_index[0]-1]:
                        new_bot = np.zeros((len(xbot[yCP_index[0]:]),2))
                        for n in range(len(new_bot)):
                            new_bot[n,[0]] = xbot[xCP_index[0]+n]
                            new_bot[n,[1]] = ybot[yCP_index[0]+n]
                    else:
                        new_bot = np.zeros((len(xbot[:yCP_index[0]]),2))
                        for n in range(len(new_bot)):
                            new_bot[n,[0]] = xbot[n]
                            new_bot[n,[1]] = ybot[n]
                else:
                    raise 'indexes of x and y values of the contact point are not the same'

                # combine new_bot with top_array to give the isolated drop contour without surface
                if 0:
                    top_array = np.zeros((len(xtop),2))
                    for n in range(len(xtop)):
                        top_array[n,[0]] = xtop[n]
                        top_array[n,[1]] = ytop[n]

                new_halfdrop = np.concatenate((top,new_bot))

                # re-order to check that the error was at the surface line
                xx,yy = sort_to_line(new_halfdrop[:,[0]],new_halfdrop[:,[1]])
                if len(xx)<len(new_halfdrop): #then the error was in the top 90% of the drop
                    print('Checking top 90% of contour...')
                    new_top, _ = two_opt(top)
                    new_halfdrop = np.concatenate((new_top,new_bot))
                    xx,yy = sort_to_line(new_halfdrop[:,[0]],new_halfdrop[:,[1]])


            else:  # if sort_to_line worked as expected
                # find the indexs of the contact point and chop off the ends
                xCP_index = [i for i, j in enumerate(xx) if j == xCP]
                #print('xCP_index is: ',xCP_index)
                yCP_index = [i for i, j in enumerate(yy) if j == yCP]
                #print('yCP_index is: ',yCP_index)

                new_halfdrop = np.zeros((len(xx),2))
                for n in range(len(xx)):
                    new_halfdrop[n,[0]]=xx[n]
                    new_halfdrop[n,[1]]=yy[n]
                #print('first 3 points of new_halfdrop are: ',new_halfdrop[:3])
                #print('length of new_halfdrop is: ',len(new_halfdrop))

                if xCP_index == yCP_index:
                    if new_halfdrop[xCP_index[0]+1][1]>new_halfdrop[xCP_index[0]-1][1]:
                        new_halfdrop = new_halfdrop[xCP_index[0]:]
                    else:
                        new_halfdrop = new_halfdrop[:xCP_index[0]+1]
                else:
                    raise_error = True
                    for x in xCP_index:
                        for y in yCP_index:
                            if x==y:
                                raise_error = False
                                xCP_index = [x]
                                yCP_index = [y]
                                #print('indexes of the CP are: ',xCP_index[0],', ',yCP_index[0])
                                if new_halfdrop[xCP_index[0]+1][1]>new_halfdrop[xCP_index[0]-1][1]:
                                    new_halfdrop = new_halfdrop[xCP_index[0]:]
                                else:
                                    new_halfdrop = new_halfdrop[:xCP_index[0]+1]
                    if raise_error == True:
                        print('The index of the contact point x value is: ', new_halfdrop[xCP_index])
                        print('The index of the contact point y value is: ', new_halfdrop[yCP_index])
                        raise 'indexes of x and y values of the contact point are not the same'

        if counter == 0:
            drops[counter] = new_halfdrop[::-1]
        else:
            drops[counter] = new_halfdrop

        if 0: #display
            plt.title('outputted halfdrop')
            plt.plot(new_halfdrop[:,0],new_halfdrop[:,1])
            plt.show()
            plt.close()

        counter+=1

    # reflect the left drop and combine left and right

    profile = np.empty((len(drops[0])+len(drops[1]),2))
    for i,n in enumerate(drops[0]):
        flipped = n
        flipped[0] = -flipped[0]
        profile[i] = flipped
    for i,n in enumerate(drops[1]):
        profile[len(drops[0])+i] = n
    CPs[0][0] = -CPs[0][0]

    if 0:
        jet= plt.get_cmap('jet')
        colors = iter(jet(np.linspace(0,1,len(profile))))
        for k in profile:
            plt.plot(k[0],k[1], 'o',color=next(colors))
        plt.title('final output')
        #plt.plot(profile[:,0],profile[:,1],'b')
        plt.show()
        plt.close()

        plt.title('final output')
        plt.plot(profile[:,0],profile[:,1],'b')
        plt.show()
        plt.close()

    # flip upside down again so that contour follows image indexing
    # and transform to the right so that x=0 is no longer in line with apex
    for coord in profile:
        coord[1] = -coord[1]
        coord[0] = coord[0] + xapex
    for n in [0,1]:
        CPs[n][1] = -CPs[n][1]
        CPs[n][0] = CPs[n][0] + xapex

    # flip contour back to original orientation
    for coord in coords:
        coord[1] = -coord[1]

    return profile,CPs

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

def cluster_OPTICS(sample, out_style='coords',xi=None,eps=None,verbose=0):
    """Takes an array (or list) of the form [[x1,y1],[x2,y2],...,[xn,yn]].
    Clusters are outputted in the form of a dictionary.

    If out_style='coords' each dictionary entry is a group, and points are outputted in coordinate form.
    If out_xy='xy' there are two dictionary entries for each group, one labeled as nx and one as ny
    (where n is the label of the group)

    If xi (float between 0 and 1) is not None and eps is None, then the xi clustering method is used.
    The optics algorithm defines clusters based on the minimum steepness on the reachability plot.
    For example, an upwards point in the reachability plot is defined by the ratio from one point to
    its successor being at most 1-xi.

    If eps (float) is not None and xi is None, then the dbscan clustering method is used. Where eps is the
    maximum distance between two samples for one to be considered as in the neighborhood of the other.

    https://stackoverflow.com/questions/47974874/algorithm-for-grouping-points-in-given-distance
    https://scikit-learn.org/stable/modules/generated/sklearn.cluster.OPTICS.html
    """
    if eps != None and xi==None:
        clustering = OPTICS(min_samples=2,cluster_method = 'dbscan',eps = eps).fit(sample) # cluster_method changed to dbscan (so eps can be set)
    elif xi != None and eps==None:
        clustering = OPTICS(min_samples=2,xi=xi).fit(sample) # original had xi = 0.05, xi as 0.1 in function input
    else:
        raise 'Error: only one of eps and xi can be chosen but not neither nor both'
    groups = list(set(clustering.labels_))

    if verbose==2:
        print(clustering.labels_)
    elif verbose==1:
        print(groups)
    elif verbose==0:
        pass

    dic = {}
    for n in groups:
        if n not in dic:
            dic[n] = []
        for i in range(len(sample)):
            if clustering.labels_[i] == n:
                dic[n].append(sample[i])

    # separate points and graph
    dic2={}
    for k in dic.keys():
        x = []
        y = []
        for i in range(len(dic[k])):
            x.append(dic[k][i][0])
        dic2[str(k)+'x'] = x
        for i in range(len(dic[k])):
            y.append(dic[k][i][1])
        dic2[str(k)+'y'] = y


    if out_style=='coords':
        return dic
    elif out_style=='xy':
        return dic2
