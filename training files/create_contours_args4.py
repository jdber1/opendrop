""" give inputs to python script from command line """

import argparse
import sys

import os
import numpy as np
import matplotlib
import cv2
import matplotlib.pyplot as plt

import time
import psutil
from scipy.integrate import odeint
import io #for saving to memory
import pickle

def yl_eqs(y, x, Bo):
    # Here U is a vector such that y=U[0] and z=U[1]. This function should return [y', z']
    return [2 + Bo * y[2] - np.sin(y[0]) / (y[1] + 1e-14), np.cos(y[0]), np.sin(y[0])]

def draw_drop(angle,
             Bo,
             scaler,
             roughness,
             N_pts_drop,
             dpi=256,
             save_dir=None,
             debug=False):
    """Creates an image for a set of parameters.

    min_angle is the lower bound of the possible contact angles
    max_angle is the upper bound of the possible contact angles
    N_angles is the number of images of difference contact angles created, the contact angles of these drops will
        be evenly spaced between the lower and upper bounds, inclusive of bound values
    min_Bo, max_Bo, and N_Bo alter the Bond number parameter of the dataset
    min_scaling, max_scaling, N_scaled_drops alter the scaling of the drop within the image, acting as a proxy
        resolution parameter
    min_roughness, max_roughness, and N_roughness alter the roughness of the baseline. 0 roughness is a perfectly
        smooth baseline, while 1e-2 is the recomended maximum value.
    N_pts_drop is the number of points used when drawing the shape of the halfdrop contour after solving the Young-
        Lacplace equation. A number significantly larger than the resolution of the image is recommended, so that the
        limiting value is the saved images resolution rather than the resolution of the solution to the Young-Laplace
        equation.
    debug (True or Flase). Set to true to visualise outputs while debugging.
    """

    s0 = [0, 0, 0]
    # the second term in s converts the angle to radians
    s = np.linspace(0, np.pi * angle / 180, N_pts_drop)
    # s = np.linspace(0, (np.pi*angle/180), N_pts_drop)
    # odeint solves ds0/ds = yl_eqs(s0,s)
    # soln is an array of triplet arrays
    soln = odeint(yl_eqs, s0, s, args=(Bo,))

    # phi is all the 0th terms of soln in degrees
    phi = 180 * soln[:, 0] / np.pi

    for i in range(1, len(phi)):
        if phi[i] < phi[i - 1]:
            phi[i] = phi[i] + 180.

    # X values of the contour are the 1th values of soln, X values exist between 0 and 1
    # Z values of the contour are the 2th values of soln
    X = soln[:, 1]
    Z = soln[:, 2]

    # Chops of the values on the contour which over-reach the set contact angle
    X = X[phi <= angle]
    Z = Z[phi <= angle]

    # flips Z coords so that the apex of drop is the max Z value
    Z = -Z + max(Z)

    # This keeps the solution within the desired bounds
    V = np.trapz(Z, X * X)
    L = scaler * V ** (1. / 3)
    X = X / L
    Z = Z / L
    Vnew = np.trapz(Z, X * X)

    X = X / max(Z)
    Z = Z / max(Z)  # normalize so that apex is at z=1

    if debug:  # plot contour
        plt.plot(X, Z, '-')
        plt.title('Theoretical halfdrop contour')
        plt.gca().set_aspect('equal', adjustable='box')
        plt.show()
        plt.close()
        print('X: \n',X)


    shape_scale = 1.5  # alter the x-axis size so that the baseline fits in the image
    if 2*max(X) > 1.5 * max(Z):
        #if true, drop will be too wide for frame before it is too tall
        img_width = 2 * max(X) * 4/3 * scaler
        img_height = img_width / shape_scale
        shift = (32 / 1024) * img_height  # baseline is a bit above bottom of frame
        xlim = [(-img_width / 2), (img_width / 2)]
        ylim = [-shift, img_height - shift]
    else:
        # drop must fit into the frame vertically
        img_height = max(Z) * 4/3 * scaler  # top of drop with some room and multiply scaler
        max_img_width = img_height * shape_scale  # from scaling difference in HD images
        shift = (32 / 1024) * img_height  # baseline is a bit above bottom of frame
        ylim = [-shift, img_height - shift]
        xlim = [(-max_img_width / 2), (max_img_width / 2)]
        #xlim = [(-max_img_width / 2), (max_img_width / 2)]
        img_width = xlim[1] - xlim[0]

    if debug:  # check that scaling is correct, should be 1:1.5

        img_height = ylim[1] - ylim[0]
        print('ratio of y to x is ', img_height / img_height, ' : ', img_width / img_height)  # correct
        # print('Angle is '+str(angle)+'\nBond number is:'+str(Bo)+'\nScaler is '+str(scaler))

    if roughness >= 0:# draw surface - named here as baseline
        baselinex = np.linspace(xlim[0], xlim[1], 100)
        # have baseline extend one extra point in both directions in case randomisation moves x coord of baseline inwards
        gap = baselinex[1]-baselinex[0]
        extra_point_left = baselinex[0]-(gap*2)
        extra_point_right = baselinex[-1]+(gap*2)
        baselinex = np.array([extra_point_left] + list(baselinex) + [extra_point_right])
        baselinez = []
        for n in range(102):
            baselinez.append(shift)
        Z = Z + shift

        coords_right = np.array(list(zip(X,Z)))
        coords_left = np.array(list(zip(-X,Z)))
        coords = np.concatenate((coords_left,coords_right), axis=0)

        # roughen surface with randomisation
        flag = False
        surface_max_plus = (roughness * L * 1.5) + shift # *2 to give room for error
        X_near_surface = np.array([x for x, z in coords if z <= surface_max_plus])

        for i in range(len(baselinex[:])):
            dpX = float(np.random.uniform(-roughness * L, roughness * L ))
            dpZ = float(np.random.uniform(-roughness * L, roughness * L ))
            pX = baselinex[i]
            pZ = baselinez[i]
            if np.min(X_near_surface) <= (pX + dpX) <= np.max(X_near_surface):#for surface line near contact points
                baselinex[i] = pX + dpX
                baselinez[i] = pZ #- abs(dpZ)
            else:
                baselinex[i] = pX + dpX
                baselinez[i] = pZ + dpZ
    else: #if roughness is negative - surface is reflective
        ref_ratio = -roughness
        # get the bottom section of the existing drop contour
        div_line = (max(Z) - min(Z))*ref_ratio
        coords = np.column_stack((X,Z))
        reflection = coords[coords[:,1] < div_line][::-1]
        reflection[:,1] = -reflection[:, 1]
        reflection_height = abs(max(reflection[:,1])) - abs(min(reflection[:,1]))
        reflection[:,1] = reflection[:,1] + (shift - min(reflection[:,1])) # raise into frame
        if debug:
            jet= plt.get_cmap('jet')
            colors = iter(jet(np.linspace(0,1,len(reflection))))
            for k in reflection:
                plt.plot(k[0],k[1], 'o',color=next(colors))
            plt.title('Reflection in order')
            plt.show()
            plt.close()

        Z = Z + shift + (max(reflection[:,1]) - min(reflection[:,1])) # raise rest of drop to accomodate reflection
        # add reflection line to X and Z
        X = np.append(X,reflection[:,0])
        Z = np.append(Z,reflection[:,1])
        #draw rest of surface line
        baselinex = np.linspace(xlim[0], xlim[1], 100)
        # have baseline extend one extra point in both directions in case randomisation moves x coord of baseline inwards
        gap = baselinex[1]-baselinex[0]
        extra_point_left = baselinex[0]-(gap*2)
        extra_point_right = baselinex[-1]+(gap*2)
        baselinex = np.array([extra_point_left] + list(baselinex) + [extra_point_right])
        baselinez = []
        for n in range(102):
            baselinez.append(shift)

    if debug: # show outline
        plt.title('Outline')
        plt.plot(X,Z)
        plt.show()
        plt.close()

    # save image to working memory
    plt.ioff()
    plt.fill_between(baselinex, baselinez, -100, facecolor='black', linewidth=0)
    plt.fill_betweenx(Z, -X, X, facecolor='black')
    plt.fill_between([-X[-1],X[-1]], [Z[-1],Z[-1]], -100, facecolor='black', linewidth=0)
    plt.plot([0,0],[shift, -100], color='black', linewidth=1)
    plt.axis('equal')
    plt.xlim(xlim)
    plt.ylim(ylim)
    plt.axis('off')

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=dpi, bbox_inches='tight',pad_inches=0)# 256
    buf.seek(0)
    img_arr = np.frombuffer(buf.getvalue(), dtype=np.uint8)
    img = cv2.imdecode(img_arr, 1)
    plt.close()
    buf.close()

    if debug:
        plt.figure(figsize=(10,10))
        plt.title('Drawn drop')
        plt.imshow(img)
        plt.show()
        plt.close()

    return img

def squish_contour(contour: np.ndarray) -> np.ndarray:
    contour = _squish_contour_one_way(contour)
    contour = _squish_contour_one_way(np.flipud(contour))
    contour = np.flipud(contour)
    return contour

def _squish_contour_one_way(contour: np.ndarray) -> np.ndarray:
    contour = contour.copy()

    path_splice = 0
    path = np.arange(len(contour))
    objective = _polyline_l1(contour, idx=range(len(contour)))

    for i in range(-1, -len(contour), -1):
        path_splice_i = path_splice
        path_i = path
        objective_i = objective
        decreasing = False

        for j in range(path_splice, len(contour)):
            path_splice_ij = j
            path_ij = np.concatenate((path[:path_splice_ij], [i], path[path_splice_ij:-1]))
            objective_ij = _polyline_l1(contour, path_ij)

            if objective_ij < objective_i:
                decreasing = True
                path_i = path_ij
                path_splice_i = j
                objective_i = objective_ij
            elif objective_ij > objective_i and decreasing:
                break

        if objective_i < objective:
            path = path_i
            path_splice = path_splice_i
            objective = objective_i
        elif objective_i > objective:
            break

    squished = contour[path]
    squished = _realign_squished_contour(squished)

    return squished

def _polyline_l1(polyline: np.ndarray, idx) -> float:
    diff = np.diff(polyline[idx], axis=0)
    length = np.sum(abs(diff))
    return length

def _realign_squished_contour(curve: np.ndarray) -> np.ndarray:
    dists = np.sum(abs(curve - np.roll(curve, shift=1, axis=0)), axis=1)
    start_idx = dists.argmax()
    return np.roll(curve, shift=-start_idx, axis=0)

def extract_edges_CV(img):
    '''
    give the image and return a list of [x.y] coordinates for the detected edges

    '''
    IGNORE_EDGE_MARGIN = 1
    threshValue = 50
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, thresh = cv2.threshold(gray,threshValue,255,cv2.THRESH_BINARY)
    #ret, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
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
    #drop_profile_squish = squish_contour(drop_profile)

    # Ignore points of the drop profile near the edges of the drop image
    width, height = img.shape[1::-1]
    if not (width < IGNORE_EDGE_MARGIN or height < IGNORE_EDGE_MARGIN):
        mask = ((IGNORE_EDGE_MARGIN < drop_profile[:, 0]) & (drop_profile[:, 0] < width - IGNORE_EDGE_MARGIN) &
            (IGNORE_EDGE_MARGIN < drop_profile[:, 1]) & (drop_profile[:, 1] < height - IGNORE_EDGE_MARGIN))
        drop_profile = drop_profile[mask]

    return drop_profile

def prepare_contour(coords, given_input_len=1100, right_only=False):
    """Take the contour of the whole drop, and chop it into left and right sides ready for model input"""
    coords[:,1] = - coords[:,1] # flip
    # isolate the top of the contour so excess surface can be deleted
    percent = 0.15
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

        # zero padd contours
        if given_input_len == None:
            input_len = len(X)
        else:
            input_len = given_input_len

        coordinates = []

        #if len(X) > global_max_len:
        #    global_max_len = len(X)

        if len(X)>input_len:
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

    if right_only == True:
        pred_ds = CV_contours[1]
    else:
        pred_ds = np.zeros((2,input_len,2))
        for counter in [0,1]:
            pred_ds[counter] = CV_contours[counter]

    return pred_ds

def create_contour(angle,
                  Bo,
                  scaler,
                  roughness,
                  savedir='./',
                  input_len=1100,
                  display=False):
    filename = filename = str(angle) + "_" + str(Bo) + "_" + str(scaler) + "_" + str(roughness) + "_.npy"

    drop = draw_drop(angle, Bo, scaler, roughness, 5000, debug=display)

    contour = extract_edges_CV(drop)
    right = prepare_contour(contour, given_input_len=None, right_only=True)

    if display==True:
        plt.plot(right[:,0],right[:,1],'o')
        plt.show()
        plt.close()

    return right

def create_contour_dataset(angle,
                            roughness,
                            min_Bo, max_Bo, N_Bos,
                            min_scaler, max_scaler, N_scalers,
                            input_len=1500,
                            save_dir=None,
                            debug=False):
    """Creates a dataset of contact angle images based on the given parameters.

    min_angle is the lower bound of the possible contact angles
    max_angle is the upper bound of the possible contact angles
    N_angles is the number of images of difference contact angles created, the contact angles of these drops will
        be evenly spaced between the lower and upper bounds, inclusive of bound values
    min_Bo, max_Bo, and N_Bo alter the Bond number parameter of the dataset
    min_scaling, max_scaling, N_scaled_drops alter the scaling of the drop within the image, acting as a proxy
        resolution parameter
    min_roughness, max_roughness, and N_roughness alter the roughness of the baseline. 0 roughness is a perfectly
        smooth baseline, while 1e-2 is the recomended maximum value.
    N_pts_drop is the number of points used when drawing the shape of the halfdrop contour after solving the Young-
        Lacplace equation. A number significantly larger than the resolution of the image is recommended, so that the
        limiting value is the saved images resolution rather than the resolution of the solution to the Young-Laplace
        equation.
    debug (True or Flase). Set to true to visualise outputs while debugging.
    """
    if debug == False: # uncomment this big when running on server
        matplotlib.use('Agg')

    start_time = time.time()
    psutil.cpu_percent(interval=0)
    psutil.virtual_memory()

    Bos = np.linspace(min_Bo, max_Bo, N_Bos)
    print('Dataset includes ', N_Bos, ' drops of bond numberss between ', min_Bo, ' and ', max_Bo)

    scalers = np.linspace(min_scaler, max_scaler, N_scalers)
    print('Dataset includes ', N_scalers, ' drops with scaling values  between ', min_scaler, ' and ',
          max_scaler)

    print('Total size of data set is :',N_Bos * N_scalers)
    print()

    dst = 'angle'+str(angle)+'_BondNumbers'+str(min_Bo)+'-'+str(max_Bo)+'_'+str(N_Bos)+'_scalers'+str(min_scaler)+'-'+str(max_scaler)+'_'+str(N_scalers)+'_roughness'+str(roughness)
    if debug == False and save_dir is not None:
        assert (not os.path.isfile(str(save_dir)+str(dst)+'.pkl'))  # make sure the directory does not exist, to avoid confusion

    created = 0

    ds = {}


    for i, Bo in enumerate(Bos):
        for j, scaler in enumerate(scalers):
            key = str(angle)+'_'+str(Bo)+'_'+str(scaler)+'_'+str(roughness)
            ds[key] = create_contour(angle,Bo,scaler,roughness,input_len=input_len,display=debug)

    # Create a single directory if it doesn't exist
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    else:
        #dst = 'data'+str(a)+'_'+str(b)+'_'+note+model_letter+'_'+str(drops)+'_scaled'+str(N_scaled_drops)
        #np.save(file=dst,arr=contours)
        with open(save_dir + dst + '.pkl', 'wb') as f:
            pickle.dump(ds, f, pickle.HIGHEST_PROTOCOL)
        print('Contours saved to: ',save_dir+dst+'.pkl')
    print("%s seconds since starting " % (time.time() - start_time))
    return ds

def positive_float(value):
    '''
    Type checking for positive floats passed to the command-line parser

    :param value: Input that is to be type-checked (scalar)
    :return: Input cast to a float
    :raises ArgumentTypeError: If the input is less than, or equal to 0 or
                               cannot be cast to a float
    '''
    if float(value) <= 0:
        raise argparse.ArgumentTypeError(f'{value} is an invalid positive '
                                         'float value')
    return float(value)

def non_negative_float(value):
    '''
    Type checking for non-negative floats passed to the command-line parser

    :param value: Input that is to be type-checked (scalar)
    :return: Input cast to a float
    :raises ArgumentTypeError: If the input is less than 0 or cannot be cast
                               to a float
    '''
    if float(value) < 0:
        raise argparse.ArgumentTypeError(f'{value} is an invalid positive '
                                         'float value')
    return float(value)

def contact_angle(value):
    '''
    Type checking for contact angles passed to the command-line parser

    :param value: Input that is to be type-checked (scalar)
    :return: Input cast to a float
    :raises ArgumentTypeError: If the input is less than 0, greater than 180,
                                or cannot be cast to a float
    '''
    if float(value) <= 0:
        raise argparse.ArgumentTypeError(f'{value} is an invalid contact '
                                         'angle value')
    if float(value) > 180:
        raise argparse.ArgumentTypeError(f'{value} is an invalid contact '
                                         'angle value')
    return float(value)

def non_negative_integer(value):
    '''
    Type checking for number of contact angles per degree passed to the
    command-line parser

    :param value: Input that is to be type-checked (scalar)
    :return: Input cast to a positive integer
    :raises ArgumentTypeError: If the input is less than 0, or cannot be cast to
                               a non-negative interget
    '''
    if int(value) < 0:
        raise argparse.ArgumentTypeError(f'{value} is an invalid integer'
                                         'angle value')

    return int(value)

def parse_cmdline(argv=None):
    '''
    Extract command line arguments to change program execution

    :param argv: List of strings that were passed at the command line
    :return: Namespace of arguments and their values
    '''
    parser = argparse.ArgumentParser(description='Create a dataset of synthetic'
                                     ' contact angle measurement images for '
                                     'the given parameters')
    parser.add_argument('save_dir', help='Relative or absolute path to '
                                     'the desired directory where synthetic'
                                     ' images will be saved. If the directory '
                                     ' does not exist then one will be created.',
                        default='./')
    parser.add_argument('-a', '--angle', type=contact_angle,
                        help='The desired contact angle of the synthetic drop',
                        action='store', dest='angle')
    parser.add_argument('-b', '--bond_number', type=non_negative_float,
                        help='The desired Bond number of the synthetic drop',
                        default=0, action='store', dest='bond_number')
    parser.add_argument('-s', '--scale', type=positive_float,
                        help='The scale of the synthetic drop image. At a value'
                        ' of 1 the drop occupies a majority of the image. '
                        'Increasing the scale value makes the drop smaller. '
                        'The recommended maximum value is 10.',
                        default=1, action='store', dest='scale')
    parser.add_argument('-r', '--roughness', type=float,
                        help='The desired roughess of the surface in the '
                        'synthetic drop image. A value of 0 will give a smooth '
                        ' surface. The recommended maximum value is 1e-2.',
                        default=0, action='store', dest='roughness')
    args = parser.parse_args(argv)

    return args

def main(argv=None):
    '''Create a pkl file of a single angle and single roughness value, with 21
    scaler and 11 roughness values.
    '''
    args = parse_cmdline(argv)

    # Set default numerical arguments
    save_dir=str(args.save_dir)
    angle = args.angle
    bond_number = args.bond_number
    scale = args.scale
    roughness = args.roughness

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    create_contour_dataset(angle,
                   roughness,
                   0,2,21,
                   1,6,11, 
                   debug=False,
                   save_dir = save_dir)

if __name__ == '__main__':
    main()
