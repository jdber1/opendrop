cimport cython
from .cshape cimport YoungLaplaceShape as cYoungLaplaceShape, vector2f 

import numpy as np


ctypedef fused numeric:
    short
    int
    long
    float
    double
    long double


ctypedef fused universal:
    short
    int
    long
    float
    double
    long double
    short[:]
    int[:]
    long[:]
    float[:]
    double[:]
    long double[:]


cdef class YoungLaplaceShape:
    cdef cYoungLaplaceShape shape

    def __cinit__(self, double bond):
        self.shape = cYoungLaplaceShape(bond)

    def __call__(self, s):
        return self.call(s)

    def call(self, universal s):
        if universal in numeric:
            return self.call_single(s)
        elif universal in numeric[:]:
            return self.call_array(s)

    cdef call_single(self, double s):
        cdef vector2f v = self.shape(s);
        return np.array(<double[:2]> v.data())

    @cython.boundscheck(False)
    @cython.wraparound(False)
    cdef call_array(self, numeric[:] s):
        cdef double[:, :] outview;
        cdef vector2f v;
        cdef size_t i;

        out = np.empty((2, s.shape[0]))
        outview = out

        for i in range(s.shape[0]):
            v = self.shape(<double>s[i])
            outview[0, i] = v[0]
            outview[1, i] = v[1]

        return out

    def DBo(self, universal s):
        if universal in numeric:
            return self.DBo_single(s)
        elif universal in numeric[:]:
            return self.DBo_array(s)

    cdef DBo_single(self, double s):
        cdef vector2f v = self.shape.DBo(s)
        return np.array(<double[:2]> v.data())

    @cython.boundscheck(False)
    @cython.wraparound(False)
    cdef DBo_array(self, numeric[:] s):
        cdef double[:, :] outview;
        cdef vector2f v;
        cdef size_t i;

        out = np.empty((2, s.shape[0]))
        outview = out

        for i in range(s.shape[0]):
            v = self.shape.DBo(<double>s[i])
            outview[0, i] = v[0]
            outview[1, i] = v[1]

        return out

    def z_inv(self, double z):
        return self.shape.z_inv(z)

    def closest(self, universal r, universal z):
        if universal in numeric:
            return self.closest_single(r, z)
        elif universal in numeric[:]:
            return self.closest_array(r, z)

    @cython.boundscheck(False)
    @cython.wraparound(False)
    cdef closest_single(self, numeric r, numeric z):
        return self.shape.closest(r, z)

    @cython.boundscheck(False)
    @cython.wraparound(False)
    cdef closest_array(self, numeric[:] r, numeric[:] z):
        if r.shape[0] != z.shape[0]:
            raise ValueError("r and z must have equal lengths")

        out = np.empty(r.shape[0])
        cdef double[:] outview = out
        for i in range(r.shape[0]):
            outview[i] = self.shape.closest(<double>r[i], <double>z[i])
        return out

    def volume(self, double s):
        return self.shape.volume(s)

    def surface_area(self, double s):
        return self.shape.surface_area(s)

    @property
    def bond(self):
        return self.shape.bond
