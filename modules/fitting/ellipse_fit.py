"""This code serves as a discrete instance of the elipse fit method of
contact angle analysis.

This is base on the circular fit code taken from the most recent version
of conan - conan-ML_cv1.1/modules/select_regions.py"""

from sklearn.cluster import OPTICS # for clustering algorithm
import scipy.optimize as opt
import numba
from scipy.spatial import distance
from scipy.integrate import solve_ivp
import numpy as np
import matplotlib.pyplot as plt
import cv2
from matplotlib.patches import Ellipse
import math
import time

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

    # if there are any large jumps in distance, there is likely a mistake
    # therefore, the points after this jump should be ignored
    if 1:
        dists = []
        for i, point in enumerate(path):
            if i < len(path)-1:
                dists.append(distance1(path[i], path[i+1]))
        jump_idx = []
        for i, dist in enumerate(dists):
            if dist > 5:
                jump_idx.append(i)
        if len(jump_idx)>0:
            path = path[:jump_idx[0]]

    return path

def prepare_hydrophobic(coords,xi=0.8,cluster=False,display=False):
    """takes an array (n,2) of coordinate points, and returns the left and right halfdrops of the contour.
    xi determines the minimum steepness on the reachability plot that constitutes a cluster boundary of the
    clustering algorithm.
    deg is the degree of the polynomial used to describe the shape of the droplet.

    This code is adapted from the prepare module, but this version differs in that it assumes that the drop
    is hydrophobic."""
    coords = coords.astype(np.float)
    # scan for clusers to remove noise and circle from lensing effect
                ################  MAY NEED TO OPTIMIZE eps/xi TO FIND APPROPRIATE GROUPINGS  ####################
    if cluster: # turn this off bc using synthetic drops without lensing effect
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

    if display:
        #print(dists)
        print()
        print('Max dist between points is: ',max(dists))
        print('Average dist between points is: ',sum(dists)/len(dists))
        print('20% over the Max dist is: ', max(dists)*1.2)
        print()
        print('Sort using cluster_OPTICS with an epsilon value of ',max(dists)*1.2)

    # how epsilon is chosen here is important
    #eps = (sum(dists)/len(dists))*2 # eps is 2 times the average distance between points
    eps = (sum(dists)/len(dists))*1.5 # eps is 2.5 times the average distance between points
    input_contour = longest
    dic,dic2 = cluster_OPTICS(input_contour,eps=eps),cluster_OPTICS(input_contour,out_style='xy',eps=eps)

    #print("number of groups: ",len(list(dic.keys())))
    if display:
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

        if 1: # plot the bottom 10% of the contour
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

def extract_edges_CV(img):
    '''
    give the image and return a list of [x.y] coordinates for the detected edges

    '''
    IGNORE_EDGE_MARGIN = 1
    img = img.astype("uint8")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    #ret, thresh = cv2.threshold(gray,threshValue,255,cv2.THRESH_BINARY)
    ret, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
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
    return output

def rot( a ):
    """
    simple rotation matrix in 2D
    """
    return np.array(
        [ [ +np.cos( a ), -np.sin( a ) ],
          [ +np.sin( a ), +np.cos( a ) ] ]
    )

def fit_ellipse( x, y ):
    """
    main fit from the original publication:
    http://nicky.vanforeest.com/misc/fitEllipse/fitEllipse.html
    """
    x = x[ :, np.newaxis ]
    y = y[ :, np.newaxis ]
    D =  np.hstack( ( x * x, x * y, y * y, x, y, np.ones_like( x ) ) )
    S = np.dot( D.T, D )
    C = np.zeros( [ 6, 6 ] )
    C[ 0, 2 ] = +2
    C[ 2, 0 ] = +2
    C[ 1, 1 ] = -1
    E, V =  np.linalg.eig( np.dot( np.linalg.inv( S ), C ) )
    n = np.argmax( np.abs( E ) )
    #n = np.argmax( E )
    a = V[ :, n ]
    return a

def ell_parameters( a ):
    """
    New function substituting the original 3 functions for
    axis, centre and angle.
    We start by noting that the linear term is due to an offset.
    Getting rid of it is equivalent to find the offset.
    Starting with the Eq.
    xT A x + bT x + c = 0 and transforming x -> x - t
    we get a new linear term. By demanding that this term vanishes
    we get the Eq.
    b = (AT + A ) t.
    Hence, an easy way to write down how to get t
    """
    RAD = 180. / np.pi
    DEGREE = 1. / RAD

    A = np.array( [ [ a[0], a[1]/2. ], [ a[1]/2., a[2] ] ] )
    b = np.array( [ a[3], a[4] ] )
    t = np.dot( np.linalg.inv( np.transpose( A ) + A ), b )
    """
    the transformation changes the constant term, which we need
    for proper scaling
    """
    c = a[5]
    cnew =  c - np.dot( t, b ) + np.dot( t, np.dot( A, t ) )
    Anew = A / (-cnew)
    # ~cnew = cnew / (-cnew) ### debug only
    """
    now it is in the form xT A x - 1 = 0
    and we know that A is a rotation of the matrix
        ( 1 / a²   0 )
    B = (            )
        ( 0   1 / b² )
    where a and b are the semi axes of the ellipse
    it is hence A = ST B S
    We note that rotation does not change the eigenvalues, which are
    the diagonal elements of matrix B. Moreover, we note that
    the matrix of eigenvectors rotates B into A
    """
    E, V = np.linalg.eig( Anew )
    """
    so we have
    B = VT A V
    and consequently
    A = V B VT
    where V is of a form as given by the function rot() from above
    """
    # ~B = np.dot( np.transpose(V), np.dot( Anew, V ) ) ### debug only
    phi = np.arccos( V[ 0, 0 ] )
    """
    checking the sin for changes in sign to detect angles above 180°
    """
    if V[ 0, 1 ] < 0:
        phi = 2 * np.pi - phi
    ### cw vs ccw and periodicity of pi
    phi = -phi % np.pi

#    for i in range(len(E)):
#        if E[i]<0:
#            E[i]=0.1

    return np.sqrt( 1. / E ), phi * RAD, -t
    """
    That's it. One might put some additional work/thought in the 180°
    and cw vs ccw thing, as it is a bit messy.
    """

def ellipse_line_intersection(xc, yc, a, b, theta, x0, y0, x1, y1, display=False):
    """
    Finds the intersection between an ellipse and a line defined by two points.

    Parameters:
    xc (float): X-coordinate of the center of the ellipse.
    yc (float): Y-coordinate of the center of the ellipse.
    a (float): Length of the semi-major axis of the ellipse.
    b (float): Length of the semi-minor axis of the ellipse.
    theta (float): Angle of rotation of the ellipse in radians.
    x0 (float): X-coordinate of the first point along the line.
    y0 (float): Y-coordinate of the first point along the line.
    x1 (float): X-coordinate of the second point along the line.
    y1 (float): Y-coordinate of the second point along the line.
    display (Boolean): Set to True to show figures

    Returns:
    tuple: A tuple containing two tuples, where each inner tuple contains the X and Y coordinates of the intercept and the gradient of the ellipse at the intercept.

    """
    # Plot the ellipse and the baseline
    if display:
        ell = Ellipse(
        [xc,yc], 2 * a, 2 * b, theta,
        facecolor=( 1, 0, 0, 0 ), edgecolor=( 1, 0, 0, 1 ))
        fig = plt.figure()
        ax = fig.add_subplot( 1, 1, 1 )
        ax.add_patch( ell )
        ax.plot(x0, y0, 'yo')
        ax.plot(x1, y1, 'go')
        ax.plot()
        plt.title('Drawn ellipse with line points in green and yellow')
        plt.gca().invert_yaxis()
        plt.show()
        plt.close()

    # Calculate the slope and intercept of the line
    m = (y1 - y0) / (x1 - x0)
    c = y0 - m * x0

    # equation for ellipse in quadratic coefficient form
    A = np.sin(theta)**2/b**2 + np.cos(theta)**2/a**2
    B = -2*np.sin(theta)*np.cos(theta)/b**2 + 2*np.sin(theta)*np.cos(theta)/a**2
    C = np.cos(theta)**2/b**2 + np.sin(theta)**2/a**2
    D = - 2*xc*np.sin(theta)**2/b**2 + 2*yc*np.sin(theta)*np.cos(theta)/b**2 - 2*xc*np.cos(theta)**2/a**2 - 2*yc*np.sin(theta)*np.cos(theta)/a**2
    E = 2*xc*np.sin(theta)*np.cos(theta)/b**2 - 2*yc*np.cos(theta)**2/b**2 - 2*xc*np.sin(theta)*np.cos(theta)/a**2 - 2*yc*np.sin(theta)**2/a**2
    F = -1 + xc**2*np.sin(theta)**2/b**2 - 2*xc*yc*np.sin(theta)*np.cos(theta)/b**2 + yc**2*np.cos(theta)**2/b**2 + xc**2*np.cos(theta)**2/a**2 + 2*xc*yc*np.sin(theta)*np.cos(theta)/a**2 + yc**2*np.sin(theta)**2/a**2

    # sub (mx + b) in for y, expand and simplify
    A_new = A + B*m + C*m**2
    B_new = B*c + 2*C*m*c + D + E*m
    C_new = C*c**2 + E*c + F

    # Calculate the discriminant of the quadratic equation
    disc = B_new**2 - 4 * A_new * C_new

    # If the discriminant is negative, there are no intercepts
    if disc < 0:
        print("The line does not intersect the ellipse.")
        return None

    # If the discriminant is zero, there is one intercept
    elif disc == 0:
        x_int = -B_new / (2 * A_new)
        y_int = m * x_int + c
        x_int_rot = x_int * np.cos(theta) - y_int * np.sin(theta)
        y_int_rot = x_int * np.sin(theta) + y_int * np.cos(theta)
        grad = -(np.cos(theta)**2 * x_int_rot) / (np.sin(theta)**2 * y_int_rot)

        return ((x_int, y_int, grad),)

    # If the discriminant is positive, there are two intercepts
    else:
        x_int_1 = (-B_new + np.sqrt(disc)) / (2 * A_new)
        x_int_2 = (-B_new - np.sqrt(disc)) / (2 * A_new)
        y_int_1 = m * x_int_1 + c
        y_int_2 = m * x_int_2 + c

        grad_1 = -(2*((-xc + x_int_1)*np.sin(theta) + (-yc + y_int_1)*np.cos(theta))*np.sin(theta)/b**2 + 2*((-xc + x_int_1)*np.cos(theta) + (-yc + y_int_1)*np.sin(theta))*np.cos(theta)/a**2)/(2*((-xc + x_int_1)*np.sin(theta) + (-yc + y_int_1)*np.cos(theta))*np.cos(theta)/b**2 + 2*((-xc + x_int_1)*np.cos(theta) + (-yc + y_int_1)*np.sin(theta))*np.sin(theta)/a**2)
        grad_2 = -(2*((-xc + x_int_1)*np.sin(theta) + (-yc + y_int_2)*np.cos(theta))*np.sin(theta)/b**2 + 2*((-xc + x_int_2)*np.cos(theta) + (-yc + y_int_2)*np.sin(theta))*np.cos(theta)/a**2)/(2*((-xc + x_int_2)*np.sin(theta) + (-yc + y_int_2)*np.cos(theta))*np.cos(theta)/b**2 + 2*((-xc + x_int_2)*np.cos(theta) + (-yc + y_int_2)*np.sin(theta))*np.sin(theta)/a**2)

        return ((x_int_1, y_int_1, grad_1), (x_int_2, y_int_2, grad_2))

def ellipse_closest_point(xp, yp, xc, yc, a, b, th, n=1000, display=False):
    """
    xp (float): The x-coordinate of the reference point
    yp (float): The y-coordinate of the reference point
    xc (float): The x-coordinate of the ellipse's center.
    yc (float): The y-coordinate of the ellipse's center.
    a (float): The semi-major axis length of the ellipse.
    b (float): The semi-minor axis length of the ellipse.
    th (float): The rotation angle of the ellipse in degrees.
    n (int): The number of discrete points used to draw the ellipse.
    display (Boolean): Set to True to output figures and information.

    Returns:
        The distance between the reference point and the ellipse edge, and
        the coordinates of the closest point on the ellipse edge.

    """

    t = np.linspace(0, 2 * np.pi, n)

    x = xc + a * np.cos(t) * np.cos(np.deg2rad(th)) - b * np.sin(t) * np.sin(np.deg2rad(th))
    y = yc + a * np.cos(t) * np.sin(np.deg2rad(th)) + b * np.sin(t) * np.cos(np.deg2rad(th))

    #tRandom = np.random.randint(n)

    #xp = x[tRandom]
    #yp = y[tRandom]

    dist = np.sqrt((x - xp) ** 2 + (y - yp) ** 2)
    idx = list(dist).index(min(dist))

    #ddistdt = ((b ** 2 - a ** 2) * np.cos(t) + a * np.sin(np.deg2rad(th)) * yp - a * np.sin(np.deg2rad(th)) * yc + a * np.cos(np.deg2rad(th)) * xp - a * np.cos(np.deg2rad(th)) * xc) * np.sin(t) + ((-b * np.cos(np.deg2rad(th)) * yp) + b * np.cos(np.deg2rad(th)) * yc + b * np.sin(np.deg2rad(th)) * xp - b * np.sin(np.deg2rad(th)) * xc) * np.cos(t)
    #idx = np.where(ddistdt[1:] * ddistdt[:-1] < 0)[0]  # find zeros
    #m = (ddistdt[idx + 1] - ddistdt[idx]) / (t[idx + 1] - t[idx])  # slope
    if display:
        plt.figure(1)
        plt.plot(x, y, '-', xp, yp, 'r+', x[idx], y[idx], 'r+')
        plt.xlabel('x')
        plt.ylabel('y')
        plt.title('Ellipse, Point, and Zeros')

        plt.figure(2)
        plt.plot(t, dist, 'm.', t[idx], dist[idx], 'cx')
        plt.xlabel('t')
        plt.ylabel('Distance')
        plt.title('Distance Function')

        print(f'xp: {xp}, x[idx]: {x[idx]}')
        print(f'yp: {yp}, y[idx]: {y[idx]}')
        print('Error is: ', dist[idx])

        plt.show()
        plt.close()

    return dist[idx], [x[idx],y[idx]]

def ellipse_fit_errors(contour, h, k, a, b, theta, display):
    """
    Calculates the minimum distance between a point and the edge of a rotated and translated ellipse.

    Parameters:
        contour (array): The array of x, y coordindate points
        h (float): The x-coordinate of the ellipse's center.
        k (float): The y-coordinate of the ellipse's center.
        a (float): The semi-major axis length of the ellipse.
        b (float): The semi-minor axis length of the ellipse.
        theta (float): The rotation angle of the ellipse in degrees.
        display (boolean): Set to true to show figures.

    Returns:
        dictionary: The MAE, MSE, RMSE, and maximum error of the contour as compared against the
        fitted ellipse.
    """

    errors = []

    for point in contour:
        dist2edge, edge_point = ellipse_closest_point(point[0], point[1], h, k, a, b, theta)
        errors.append(dist2edge)

    error_measures = {}

    error_measures['MAE'] = sum([abs(error) for error in errors])/len(errors)
    error_measures['MSE'] = sum([error**2 for error in errors])/len(errors)
    error_measures['RMSE'] = np.sqrt(sum([error**2 for error in errors])/len(errors))
    error_measures['Maximum error'] = max(errors)

    return error_measures

def ellipse_fit_img(img,display=False):
    """Call this function to perform the circular fit.
    For best results, peprocessing must be done before calling this function.
    """
    # begin with method specific preprocessing of img data
    start_time = time.time()

    edges_pts = extract_edges_CV(img) # array of x,y coords where lines are detected

    if display:
        plt.imshow(img)
        plt.plot(edges_pts[:,0],edges_pts[:,1])
        plt.title('drop found by hough transform')
        plt.show()
        plt.close()

    drop,CPs = prepare_hydrophobic(edges_pts,display)

    # define baseline as between the two contact points

    x = drop[:,0]
    y = drop[:,1]
    rise = CPs[1][1]-CPs[0][1]
    run = CPs[1][0]-CPs[0][0]
    slope = rise/run
    baseline = [(CPs[0][0],CPs[0][1]), slope]
    c = CPs[0][1]-(slope*CPs[0][0])
    baseline_x = np.linspace(1, img.shape[1],100)
    baseline_y = slope*baseline_x+c

    # timers
    fit_preprocessing_time = time.time() - start_time
    fit_start_time = time.time()

    #fit
    avec = fit_ellipse(x, y)
    (a, b), phi_deg, t = ell_parameters(avec)

    ell = Ellipse(
        t, 2 * a, 2 * b, phi_deg,
        facecolor=( 1, 0, 0, 0 ), edgecolor=( 1, 0, 0, 1 ))

    if display:
        print('centre points: '+str(t))
        print('a and b: '+str(a)+', '+str(b))
        print('phi (°): '+str(phi_deg))

        #plot
        fig = plt.figure()
        ax = fig.add_subplot( 1, 1, 1 )
        ax.add_patch( ell )
        ax.scatter(x ,y)
        ax.plot(baseline_x,baseline_y)
        ax.plot(CPs[0][0], CPs[0][1], 'yo')
        ax.plot(CPs[1][0], CPs[1][1], 'go')
        ax.plot()
        plt.title('Fitted ellipse')
        plt.imshow(img)
        plt.show()
        plt.close()

    # Find intercepts, and gradients at intercepts
    outputs = ellipse_line_intersection(t[0], t[1], a, b, math.radians(phi_deg), CPs[0][0], CPs[0][1], CPs[1][0], CPs[1][1])
    left, right = list(sorted(outputs, key=lambda x: x[0]))
    m_left, m_right = left[2], right[2]
    intercepts = [[left[0],left[1]],[right[0],right[1]]]

    CA = []
    for output in outputs:
        first = True
        m = output[2] - slope

        if output[1] > t[1] and first == True: #high CA angle left
            #CA.append(math.degrees(np.pi+np.arctan(m)))
            CA.append(180 - abs(math.degrees(np.arctan(m))))
        elif output[1] > t[1] and first == False: #high CA angle right
            CA.append(abs(math.degrees(np.arctan(m))))
        elif output[1] < t[1] and first == True: #low CA angle left
            CA.append(math.degrees(np.arctan(m)))
        elif output[1] < t[1] and first == False: #low CA angle right
            CA.append(math.degrees(np.pi+np.arctan(m)))


        first = False

    #if CA[0]!=CA[1]:
    #    CA[1] = 180 - CA[1]

    fit_time = time.time() - fit_start_time

    # using MAE, MSE, RMSE, max_error as error measure
    errors = ellipse_fit_errors(drop,t[0],t[1],a,b,phi_deg,display)

    analysis_time = time.time() - start_time

    timings = {}
    timings['method specific preprocessing time'] = fit_preprocessing_time
    timings['fit time'] = fit_time
    timings['analysis time'] = analysis_time

    return CA, intercepts, t, (a,b), phi_deg, errors, timings

def ellipse_fit(drop,display=False):
    """Call this function to perform the ellipse fit.
    For best results, peprocessing must be done before calling this function.

    Make sure that the drop coordinate array consists of float values.
    """

    # begin with method specific preprocessing of img data
    start_time = time.time()
    CPs = [drop[0],drop[-1]]

    # define baseline as between the two contact points

    x, y = drop[:,0], drop[:,1]
    rise = CPs[1][1]-CPs[0][1]
    run = CPs[1][0]-CPs[0][0]
    slope = rise/run
    baseline = [(CPs[0][0],CPs[0][1]), slope]
    c = CPs[0][1]-(slope*CPs[0][0])
    baseline_x = np.linspace(1, max(drop[:,0]),100)
    baseline_y = slope*baseline_x+c

    # Center estimates - it doesn't even take these
    # x estimate is where between the lowest and highest points of the top section for a hydrophobic drop
    x_m = min(x)+(max(x)-min(x))/2
    # for full contour, y estimate is the halfway between max y and min y
    y_m = min(y) + ((max(y)-min(y))/2)

    #fit
    avec = fit_ellipse(x, y)
    (a, b), phi_deg, t = ell_parameters(avec)

    ell = Ellipse(
        t, 2 * a, 2 * b, phi_deg,
        facecolor=( 1, 0, 0, 0 ), edgecolor=( 1, 0, 0, 1 ), label='Fitted ellipse')

    if display:
        print('drop contour: ',drop)
        print('centre points: '+str(t))
        print('a and b: '+str(a)+', '+str(b))
        print('phi (°): '+str(phi_deg))

        if 1:#plot
            fig = plt.figure()
            ax = fig.add_subplot( 1, 1, 1 )
            ax.add_patch( ell )
            ax.scatter(x ,y, label='contour')
            ax.plot(baseline_x,baseline_y, label='baseline')
            ax.plot(CPs[0][0], CPs[0][1], 'yo', label='left contact point')
            ax.plot(CPs[1][0], CPs[1][1], 'go', label='right contact point')
            ax.plot()
            ax.legend()
            plt.title('Fitted ellipse')
            plt.axis('equal')
            plt.show()
            plt.close()

    # Find intercepts, and gradients at intercepts
    outputs = ellipse_line_intersection(t[0], t[1], a, b, math.radians(phi_deg), CPs[0][0], CPs[0][1], CPs[1][0], CPs[1][1])
    left, right = list(sorted(outputs, key=lambda x: x[0]))
    m_left, m_right = left[2], right[2]
    intercepts = [[left[0],left[1]],[right[0],right[1]]]

    CA = []
    for output in outputs:
        first = True
        m = output[2] - slope

        if output[1] > t[1] and first == True: #high CA angle left
            #CA.append(math.degrees(np.pi+np.arctan(m)))
            CA.append(180 - abs(math.degrees(np.arctan(m))))
        elif output[1] > t[1] and first == False: #high CA angle right
            CA.append(abs(math.degrees(np.arctan(m))))
        elif output[1] < t[1] and first == True: #low CA angle left
            CA.append(math.degrees(np.arctan(m)))
        elif output[1] < t[1] and first == False: #low CA angle right
            CA.append(math.degrees(np.pi+np.arctan(m)))


        first = False

    #if CA[0]!=CA[1]:
    #    CA[1] = 180 - CA[1]

    fit_time = time.time() - start_time

    try:# using MAE, MSE, RMSE, max_error as error measure
        errors = ellipse_fit_errors(drop,t[0],t[1],a,b,phi_deg,display)
    except:
        errors = 'something went wrong fitting the ellipse...'
        print(errors)
    analysis_time = time.time() - start_time

    timings = {}
    timings['fit time'] = fit_time
    timings['analysis time'] = analysis_time

    return CA, intercepts, t, (a,b), phi_deg, errors, timings

if 0:
    IMG_PATH = '../RICOphobic_cropped.png'
    img = cv2.imread(IMG_PATH)

    angles, intercepts, center, (a,b), theta, errors, timings = ellipse_fit_img(img, display=True)
    print('angles: ', angles)
    print('intercepts: ', intercepts)
    print('center coordinates: ', center)
    print('a: ',a)
    print('b: ',b)
    print('angle of ellipse rotation: ', theta)
    print('errors: ',errors)
    print('timings: ', timings)
