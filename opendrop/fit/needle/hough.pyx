cimport cython
from libc.math cimport M_PI, sin, cos, lrint

import numpy as np


DEF ANGLE_STEPS = 200
DEF DIST_STEPS = 64


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
def hough(double[:, :] data, int diagonal):
    cdef int[:, :] votes
    cdef size_t i, theta_i, rho_i
    cdef double theta, rho
    
    # Pad the accumulator array with 0s in the second axis, this helps to find peaks at the start or end when 
    # using scipy.signal.find_peaks().
    votes_array = np.zeros(shape=(ANGLE_STEPS, DIST_STEPS + 2), dtype=np.int32)
    votes = votes_array
    
    for i in range(data.shape[1]):
        for theta_i in range(votes.shape[0]):
            theta = theta_i/<double>votes.shape[0] * M_PI
            rho = data[0][i]*sin(theta) - data[1][i]*cos(theta)
            rho_i = 1 + lrint((rho + 0.5*diagonal)/diagonal * (votes.shape[1] - 3))
            votes[theta_i, rho_i] += 1
    
    return votes_array
