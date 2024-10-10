#!/usr/bin/env python
#coding=utf-8

"""This code serves as a discrete instance of image preprocessing before contact
angle fit software is implemented

This includes automatic identification of the drop through Hough transform,
followed by cropping of the image to isolate the drop. Tilt correction is then
performed using the identified contact points of the drop.
"""



from sklearn.cluster import OPTICS # for clustering algorithm
import numpy as np
import matplotlib.pyplot as plt
import cv2
import math #for tilt_correction
from scipy import misc, ndimage #for tilt_correction

def auto_crop(img, low=50, high=150, apertureSize=3, verbose=0): # DS 08/06/23
    '''
    Automatically identify where the crop should be placed within the original
    image

    This function utilizes the opencv circular and linear Hough transfrom
    implementations to identify the most circular object in the image
    (the droplet), and center it within a frame that extends by padding to each
    side.

    :param img: 2D numpy array of [x,y] coordinates of the edges of the
                  image
    :param low: Value of the weak pixels in the dual thresholding
    :param high: Value of the strong pixels in the dual thresholding
    :param apertureSize: The aperture size variable given to cv2.Canny during
                        edge detection
    :param verbose: Integer values from 0 to 2, giving varying degrees of detail
    :return: list of [left, right, top, bottom] values for the edges of the
             bounding box
    '''


    if verbose >=1:
        print('Performing auto-cropping, please wait...')

    # find edges in the image
    gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray,low,high,apertureSize = apertureSize)

    #hough circle to find droplet - minRadius at 5% img width
    circles = cv2.HoughCircles(edges, cv2.HOUGH_GRADIENT, 1,
                              minDist=max(img.shape), #one circle
                              param1=30,
                              param2=15,
                              minRadius=int(img.shape[1]*0.02), #0.05
                              maxRadius=0)

    if circles is not None:
        circles = np.uint16(np.around(circles))
        for i in circles[0, :]:
            center = (i[0], i[1])
            radius = i[2]

            if verbose >= 2:
                circle1 = plt.Circle(center, 1, color='r')
                # now make a circle with no fill, which is good for hi-lighting key results
                circle2 = plt.Circle(center, radius, color='r', fill=False)

                ax = plt.gca()
                ax.axis('equal')

                ax.add_patch(circle1)
                ax.add_patch(circle2)

                fig = plt.gcf()
                fig.set_size_inches(10, 10)

                plt.imshow(img)
                plt.title("Hough circle")
                plt.show()
                plt.close()
    else:
        #hough circle to find droplet - minRadius at 0
        circles = cv2.HoughCircles(edges, cv2.HOUGH_GRADIENT, 1,
                                  minDist=max(img.shape), #one circle
                                  param1=30,
                                  param2=20,
                                  minRadius=0,
                                  maxRadius=0)
    if circles is not None:
        circles = np.uint16(np.around(circles))
        for i in circles[0, :]:
            center = (i[0], i[1])
            radius = i[2]

            if verbose >= 2:
                circle1 = plt.Circle(center, 1, color='r')
                # now make a circle with no fill, which is good for hi-lighting key results
                circle2 = plt.Circle(center, radius, color='r', fill=False)

                ax = plt.gca()
                ax.axis('equal')

                ax.add_patch(circle1)
                ax.add_patch(circle2)

                fig = plt.gcf()
                fig.set_size_inches(10, 10)

                plt.imshow(img)
                plt.title("Hough circle")
                plt.show()
                plt.close()
    else:
        print('Hough circle failed to identify a drop')

    #crop image based on circle found (this prevents hough line identifying the needle)
    bottom = int(center[1] + (radius * 1.2)) # add 20% padding
    if bottom>img.shape[0]:
        bottom = img.shape[0]
    top = int(center[1] - (radius * 1.2)) #add 20% padding
    if top < 0:
        top=0

    img = img[top:bottom,:]
    edges = cv2.Canny(img,50,150,apertureSize = 3)
    center = (center[0], -(center[1] - bottom)) #reassign circle center to new cropped image

    if verbose>=2:
        plt.imshow(img)
        plt.title('image after top and bottom crop')
        plt.show()
        plt.close()

    #hough lines to find baseline
    lines = cv2.HoughLines(edges,1,np.pi/180,100)

    if lines is not None: # if the HoughLines function is successful
        if verbose >= 2:
            print('shape of image: ',img.shape)
        for i,line in enumerate(lines):
            if i==0:
                rho,theta = line[0]
                a = np.cos(theta)
                b = np.sin(theta)
                x0 = a*rho
                y0 = b*rho
                x1 = int(x0)
                y1 = int(y0 + 1000*(a))
                x2 = int(x0 - img.shape[1]*(-b))
                y2 = int(y0 - 1000*(a))
                if verbose >= 2:
                    plt.title('hough approximated findings')
                    plt.imshow(img)
                    circle1 = plt.Circle(center, 1, color='r')
                    circle2 = plt.Circle(center, radius, color='r', fill=False)
                    ax = plt.gca()
                    ax.add_patch(circle1)
                    ax.add_patch(circle2)
                    fig = plt.gcf()

                    plt.plot([x1,x2],[y1,y2],'r')
                    fig = plt.gcf()
        p1,p2 = (x1,y1),(x2,y2) # baseline exists between these points
        if verbose >= 2:
            print('baseline goes from ',p1,' to ',p2)

        # now find bounds

        # find intercept of line and circle
        dx, dy = p2[0] - p1[0], p2[1] - p1[1]

        a = dx**2 + dy**2
        b = 2 * (dx * (p1[0] - center[0]) + dy * (p1[1] - center[1]))
        c = (p1[0] - center[0])**2 + (p1[1] - center[1])**2 - radius**2

        discriminant = b**2 - 4 * a * c
        if discriminant > 0:
            t1 = (-b + discriminant**0.5) / (2 * a)
            t2 = (-b - discriminant**0.5) / (2 * a)

            intersect1, intersect2 = None,None
            intersect1, intersect2 = (dx * t1 + p1[0], dy * t1 + p1[1]), (dx * t2 + p1[0], dy * t2 + p1[1])

            if intersect1 == None or intersect2 == None:
                raise 'found baseline does not intersect with found circle'

            if verbose >= 2:
                plt.plot(intersect1[0],intersect1[1],'o',color='orange')
                plt.plot(intersect2[0],intersect2[1],'o',color='orange')

                plt.show()
                plt.close()

            bottom = int(max([intersect1[1],intersect2[1]]))          #max value of intersect points
            top = int(center[1] - radius)                             #assume top of drop is in image
            if center[1] < max([intersect1[1],intersect2[1]]):
                right = int(center[0] + radius)
            else:
                right = int(max([intersect1[0],intersect2[0]]))
            if center[1] < min([intersect1[1],intersect2[1]]):
                left = int(center[0] - radius)
            else:
                left = int(min([intersect1[0],intersect2[0]]))
        else:
            # bounds is (left,right,top,bottom)
            print('No baseline-drop intercept found')
            left = int(center[0] - radius)
            right = int(center[0] + radius)
            top = int(center[1] - radius)
            bottom = int(center[1] + radius)

    else: #if the HoughLine function cannot identify a surface line, use the circle as a guide for bounds
        left = int(center[0] - radius)
        right = int(center[0] + radius)
        top = int(center[1] - radius)
        bottom = int(center[1] + radius)

    pad = int(max([right - left,bottom-top])/4)

    top -= pad
    bottom += pad
    left -= pad
    right += pad

    if left < 0:
        left = 0
    if top < 0:
        top = 0
    if bottom > img.shape[0]:
        bottom = img.shape[0]
    if right > img.shape[1]:
        right = img.shape[1]

    if verbose >= 2:
        print('lower most y coord of drop: ', bottom)
        print('upper most y coord of drop: ', top)
        print('right most x coord of drop: ', right)
        print('left most x coord of drop: ', left)

    bounds = [left,right,top,bottom]
    new_img = img[top:bottom,left:right]

    if verbose >= 1:
        plt.title('cropped drop')
        plt.imshow(new_img)
        plt.show()
        plt.close()

    return new_img, bounds

def find_intersection(baseline_coeffs, circ_params):
    '''
    Compute the intersection points between the best fit circle and best-fit
    baseline.

    For this we rely on several coordinate transformations, first a
    translation to the centerpoint of the circle and then a rotation to give
    the baseline zero-slope.

    :param baseline_coeffs: Numpy array of coefficients to the baseline
                            polynomial
    :param circ_params: centerpoint and radius of best-fit circle
    :return: (x,y) point of intersection between these two shapes
    '''
    *z, r = circ_params
    b, m = baseline_coeffs[0:2]
    # Now we need to actually get the points of intersection
    # and the angles from these fitted curves. Rather than brute force
    # numerical solution, use combinations of coordinate translations and
    # rotations to arrive at a horizontal line passing through a circle.
    # First step will be to translate the origin to the center-point
    # of our fitted circle
    # x = x - z[0], y = y - z[1]
    # Circle : x**2 + y**2 = r**2
    # Line : y = m * x + (m * z[0] + b - z[1])
    # Now we need to rotate clockwise about the origin by an angle q,
    # s.t. tan(q) = m
    # Our transformation is defined by the typical rotation matrix
    #   [x;y] = [ [ cos(q) , sin(q) ] ;
    #             [-sin(q) , cos(q) ] ] * [ x ; y ]
    # Circle : x**2 + y**2 = r**2
    # Line : y = (m*z[0] + b[0] - z[1])/sqrt(1 + m**2)
    # (no dependence on x - as expected)

    # With this simplified scenario, we can easily identify the points
    # (x,y) where the line y = B
    # intersects the circle x**2 + y**2 = r**2
    # In our transformed coordinates, only keeping the positive root,
    # this is:

    B = (m * z[0] + b - z[1]) / np.sqrt(1 + m**2)

    if B > r:
        raise ValueError("The circle and baseline do not appear to intersect")
    x_t = np.sqrt(r ** 2 - B ** 2)
    y_t = B

    # TODO:// replace the fixed linear baseline with linear
    # approximations near the intersection points

    return x_t, y_t

def cluster_OPTICS(sample, out_style='coords',xi=None,eps=None,verbose=0):
    """Takes an array (or list) of the form [[x1,y1],[x2,y2],...,[xn,yn]].
    Clusters are outputted in the form of a dictionary.

    If out_style='coords' each dictionary entry is a group, and points are outputted in as a numpy array
    in coordinate form.
    If out_xy='xy' there are two dictionary entries for each group, one labeled as nx and one as ny
    (where n is the label of the group). Each of these are 1D numpy arrays

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
                dic[n].append(list(sample[i]))
        dic[n] = np.array(dic[n])

    # separate points and graph
    dic2={}
    for k in dic.keys():
        x = []
        y = []
        for i in range(len(dic[k])):
            x.append(dic[k][i][0])
        dic2[str(k)+'x'] = np.array(x)
        for i in range(len(dic[k])):
            y.append(dic[k][i][1])
        dic2[str(k)+'y'] = np.array(y)


    if out_style=='coords':
        return dic
    elif out_style=='xy':
        return dic2

def distance1(P1, P2):
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
        nearest = min(pass_by, key=lambda x: distance1(path[-1], x))
        path.append(nearest)
        pass_by.remove(nearest)
    path = np.array(path)
    return path

def prepare_hydrophobic(coords,xi=0.8,cluster=True,display=False):
    """takes an array (n,2) of coordinate points, and returns the left and right halfdrops of the contour.
    xi determines the minimum steepness on the reachability plot that constitutes a cluster boundary of the
    clustering algorithm.
    deg is the degree of the polynomial used to describe the shape of the droplet.

    This code is adapted from the prepare module, but this version differs in that it assumes that the drop
    is hydrophobic."""
    coords = coords.astype(np.float)

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
    percent = 0.3
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

    dists = [] # find the average distance between consecutive points
    for n,co in enumerate(top_array):
        if 1<n:
            a = top_array[n]
            dist = np.linalg.norm(top_array[n]-top_array[n-1])
            dists.append(dist)

    # how epsilon is chosen here is important
    #eps = (sum(dists)/len(dists))*2 # eps is 2 times the average distance between points
    eps = (sum(dists)/len(dists))*1.5 # eps is 2.5 times the average distance between points
    if display:
        #print(dists)
        print()
        print('Max dist between points is: ',max(dists))
        print('Average dist between points is: ',sum(dists)/len(dists))
        print()
        print('Sort using cluster_OPTICS with an epsilon value of ',eps)
    input_contour = np.array(longest)
    dic = cluster_OPTICS(input_contour,eps=eps)
    if display:
        jet= plt.get_cmap('jet')
        colors = iter(jet(np.linspace(0,1,len(list(dic.keys())))))
        for k in dic.keys():
            plt.plot(dic[k][:,0],dic[k][:,1], 'o',color=next(colors))
        plt.title(str(len(dic.keys()))+' groups found by clustering with epsilon value of '+str(eps))
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

    l_drop = []
    r_drop = []
    for n in longest:
        if n[0] <= xapex:
            l_drop.append(n)
        if n[0] >= xapex:
            r_drop.append(n)
    l_drop = np.array(l_drop)
    r_drop = np.array(r_drop)

    # transpose both half drops so that they both face right and the apex of both is at 0,0
    r_drop[:,0] = r_drop[:,0] - xapex
    l_drop[:,0] = -l_drop[:,0] + xapex

    if display:
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
        new_halfdrop = sorted(halfdrop.tolist(), key=lambda x: (x[0],-x[1])) #top left to bottom right
        new_halfdrop = optimized_path(new_halfdrop)#[::-1]

        xnew_halfdrop = new_halfdrop[:,[0]].reshape(len(new_halfdrop[:,[0]]))
        ynew_halfdrop = new_halfdrop[:,[1]].reshape(len(new_halfdrop[:,[1]]))

        # isolate the bottom of the drop to help identify contact points (may not need to do this for all scenarios)
        bottom = []
        top = [] # will need this later
        #print('isolate the bottom ',percent*100,'% of the contour:') # percent defined above
        div_line_value = min(new_halfdrop[:,[1]]) + (max(new_halfdrop[:,[1]]) - min(new_halfdrop[:,[1]]))*percent
        for n in new_halfdrop:
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

        if 0: # plot the bottom 10% of the contour, check that the contour ordering is performing
            plt.plot(xbottom, ybottom, 'b,')
            plt.title('bottom 10% of the contour')
            #plt.xlim([130,200])
            plt.show()
            plt.close()

        #### Continue here assuming that the drop is hydrophobic ####
        if 1:
            # order all halfdrop points using optimized_path (very quick but occasionally makes mistakes)

            xCP = min(xbottom)
            #yCP = min([coord[1] for coord in new_halfdrop if coord[0]==xCP])
            yCP = max([coord[1] for coord in bottom if coord[0]==xCP])
            CPs[counter] = [xCP, yCP]

            if display: #check
                plt.plot(new_halfdrop[:,0],new_halfdrop[:,1])
                plt.show()
                plt.close()

            # remove surface line past the contact point
            index = new_halfdrop.tolist().index(CPs[counter]) #?

            new_halfdrop = new_halfdrop[:index+1]

            if 0:
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
            if display:
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

            if display: #display
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

                if display:
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

        if display: #display
            jet= plt.get_cmap('jet')
            colors = iter(jet(np.linspace(0,1,len(new_halfdrop))))
            for k in new_halfdrop:
                plt.plot(k[0],k[1], 'o',color=next(colors))
            plt.title('outputted halfdrop')
            plt.axis('equal')
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

    if display:
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

    # flip original contour back to original orientation
    for coord in coords:
        coord[1] = -coord[1]

    return profile,CPs

def find_contours(image):
    """
        Calls cv2.findContours() on passed image in a way that is compatible with OpenCV 4.x, 3.x or 2.x
        versions. Passed image is a numpy.array.

        Note, cv2.findContours() will treat non-zero pixels as 1 and zero pixels as 0, so the edges detected will only
        be those on the boundary of pixels with non-zero and zero values.

        Returns a numpy array of the contours in descending arc length order.
    """
    if len(image.shape) > 2:
        raise ValueError('`image` must be a single channel image')

    if CV2_VERSION >= (4, 0, 0):
        # In OpenCV 4.0, cv2.findContours() no longer returns three arguments, it reverts to the same return signature
        # as pre 3.2.0.
        contours, hierarchy = cv2.findContours(image, cv2.RETR_LIST, cv2.CHAIN_APPROX_TC89_KCOS)
    elif CV2_VERSION >= (3, 2, 0):
        # In OpenCV 3.2, cv2.findContours() does not modify the passed image and instead returns the
        # modified image as the first, of the three, return values.
        _, contours, hierarchy = cv2.findContours(image, cv2.RETR_LIST, cv2.CHAIN_APPROX_TC89_KCOS)
    else:
        contours, hierarchy = cv2.findContours(image, cv2.RETR_LIST, cv2.CHAIN_APPROX_TC89_KCOS)

    # Each contour has shape (n, 1, 2) where 'n' is the number of points. Presumably this is so each
    # point is a size 2 column vector, we don't want this so reshape it to a (n, 2)
    contours = [contour.reshape(contour.shape[0], 2) for contour in contours]

    # Sort the contours by arc length, descending order
    contours.sort(key=lambda c: cv2.arcLength(c, False), reverse=True)

    return contours

def extract_edges_CV(img, threshold_val=None, return_thresholed_value=False, display=False):
    '''
    give the image and return a list of [x.y] coordinates for the detected edges

    '''
    IGNORE_EDGE_MARGIN = 1
    img = img.astype("uint8")
    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    except:
        gray = img

    if threshold_val == None:
        #ret, thresh = cv2.threshold(gray,threshValue,255,cv2.THRESH_BINARY)
        ret, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    else:
        ret, thresh = cv2.threshold(gray,threshold_val,255,cv2.THRESH_BINARY)

    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    # Each contour has shape (n, 1, 2) where 'n' is the number of points. Presumably this is so each
    # point is a size 2 column vector, we don't want this so reshape it to a (n, 2)
    contours = [contour.reshape(contour.shape[0], 2) for contour in contours]

    # Sort the contours by arc length, descending order
    contours.sort(key=lambda c: cv2.arcLength(c, False), reverse=True)

    #Assume that the drop is the largest contour
    #drop_profile = contours[0]
    drop_profile = contours[0]

    #Put the drop contour coordinates in order (from ?? to ??)
    #drop_profile = squish_contour(drop_profile)

    # Ignore points of the drop profile near the edges of the drop image
    width, height = img.shape[1::-1]
    if not (width < IGNORE_EDGE_MARGIN or height < IGNORE_EDGE_MARGIN):
        mask = ((IGNORE_EDGE_MARGIN < drop_profile[:, 0]) & (drop_profile[:, 0] < width - IGNORE_EDGE_MARGIN) &
            (IGNORE_EDGE_MARGIN < drop_profile[:, 1]) & (drop_profile[:, 1] < height - IGNORE_EDGE_MARGIN))
        drop_profile = drop_profile[mask]

    output = []
    for coord in drop_profile:
        if list(coord) not in output:
            output.append(list(coord))
    output = np.array(output)

    if return_thresholed_value==True:
        return output, ret
    else:
        return output

def tilt_correction(img, baseline, user_set_baseline=False):
    """img is an image input
    baseline is defined by two points in the image"""

    p1,p2 = baseline[0],baseline[1]
    x1,y1 = p1
    x2,y2 = p2

    #assert(not x1 == x2 or y1 == y2)
    if y1 == y2: # image is level
        return img

    if user_set_baseline == True:
        img = img[:int(max([y1,y2])), :]

    t = float(y2 - y1) / (x2 - x1)
    rotate_angle = math.degrees(math.atan(t))
    if rotate_angle > 45:
        rotate_angle = -90 + rotate_angle
    elif rotate_angle < -45:
        rotate_angle = 90 + rotate_angle
    rotate_img = ndimage.rotate(img, rotate_angle)
    print('image rotated by '+str(rotate_angle)+' degrees')

    # crop black edges created when rotating
    width = np.sin(np.deg2rad(rotate_angle))
    side = math.ceil(abs(width*rotate_img.shape[1]))
    roof = math.ceil(abs(width*rotate_img.shape[0]))
    rotate_img_crop = rotate_img[roof:-roof,side:-side]

    return rotate_img_crop

def preprocess(img, correct_tilt=True, display=False):
    """This code serves as a discrete instance of image preprocessing before contact
    angle fit software is implemented.

    This includes automatic identification of the drop through Hough transform,
    followed by cropping of the image to isolate the drop. Tilt correction is then
    performed using the identified contact points of the drop.
    An isolated (cropped) and tilt corrected image is outputted.
    """
    # preprocessing
    img_crop, bounds = auto_crop(img.copy(),verbose=0)
    L,R,T,B = bounds
    edges_pts = extract_edges_CV(img_crop) # array of x,y coords where lines are detected

    if display:
        plt.imshow(img_crop)
        plt.plot(edges_pts[:,0],edges_pts[:,1])
        plt.title('drop found by hough transform')
        plt.show()
        plt.close()

    profile,CPs = prepare_hydrophobic(edges_pts,display=display)

    if correct_tilt:
        baseline = [CPs[0],CPs[1]]
        tilt_corrected_crop = tilt_correction(img_crop, baseline)

        if display:
            plt.imshow(tilt_corrected_crop)
            plt.title('tilt corrected and cropped image')
            plt.show()
            plt.close()

        edges_pts = extract_edges_CV(tilt_corrected_crop)
        profile,CPs = prepare_hydrophobic(edges_pts,display=display)
        return tilt_corrected_crop, profile
    else:
        return img_crop, profile

def preprocess_ML(img, display=False):
    """This code serves as a discrete instance of image preprocessing before contact
    angle fit software is implemented.

    This includes automatic identification of the drop through Hough transform,
    followed by cropping of the image to isolate the drop. Tilt correction is then
    performed using the identified contact points of the drop.
    An isolated (cropped) and tilt corrected image is outputted.
    """
    # preprocessing
    img_crop, bounds = auto_crop(img.copy(),verbose=0)
    L,R,T,B = bounds
    edges_pts = extract_edges_CV(img_crop) # array of x,y coords where lines are detected

    if display:
        plt.imshow(img_crop)
        plt.plot(edges_pts[:,0],edges_pts[:,1])
        plt.title('drop found by hough transform')
        plt.show()
        plt.close()

    profile,CPs = prepare_hydrophobic(edges_pts,display=display)

    baseline = [CPs[0],CPs[1]]
    tilt_corrected_crop = tilt_correction(img_crop, baseline)

    if display:
        plt.imshow(tilt_corrected_crop)
        plt.title('tilt corrected and cropped image')
        plt.show()
        plt.close()

    return tilt_corrected_crop

if 0: #test
    #IMG_PATH = '/Users/dgshaw/OneDrive - The University of Melbourne/experimental-image-database/Chiara-group-images/Natural/20171112JT.BMP'
    #IMG_PATH = '/Users/dgshaw/OneDrive - The University of Melbourne/experimental-image-database/Binyu-group-images/96-8.bmp'
    #IMG_PATH = '/Users/dgshaw/OneDrive - The University of Melbourne/experimental-image-database/evaporation-screenshots/Screenshot 2023-05-05 at 2.21.34 pm.png'
    #IMG_PATH = '/Users/dgshaw/cloudstor/files/models/model_v03/sensitivity_spartan_replication/sensitivity_dataset/170.0_1.5_1.0_0.0_.png'
    #IMG_PATH = '/Users/dgshaw/Library/CloudStorage/OneDrive-TheUniversityofMelbourne/experimental-image-database/Kristina/2023_05_26_RWTH_AVT_FVT_Kristina_Mielke_selected_pictures/static_contact_angle/20230328_water_solvent_1b_0_250_15_6.jpg'
    #IMG_PATH = '/Users/dgshaw/Library/CloudStorage/OneDrive-TheUniversityofMelbourne/experimental-image-database/Kristina/2023_05_26_RWTH_AVT_FVT_Kristina_Mielke_selected_pictures/static_contact_angle/20230328_water_solvent_1b_0_250_15_1.jpg'
    #IMG_PATH = '/Users/dgshaw/OneDrive - The University of Melbourne/experimental-image-database/MCFP-CA-images/CA images batch 1/Water+MOF/20221101-24h/115.553909.bmp'
    IMG_PATH = '/Users/dgshaw/OneDrive - The University of Melbourne/experimental-image-database/Current/10.bmp'

    img = cv2.imread(IMG_PATH, cv2.IMREAD_COLOR)

    if 1:
        plt.title('loaded image')
        plt.imshow(img)
        plt.show()
        plt.close()

    print('beginning preprocessing')
    img,profile = preprocess(img, display=True)

    if 1:
        plt.title('processed image')
        plt.imshow(img)
        plt.show()
        plt.close()
    print('preprocessing ended')
    print()
    print('repeating preprocessing with display off')

    img, profile = preprocess(img, display=False)
