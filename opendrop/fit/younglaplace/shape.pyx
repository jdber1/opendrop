import numpy as np

from .cshape cimport YoungLaplaceShape as cYoungLaplaceShape, vector2f 


cdef class YoungLaplaceShape:
    cdef cYoungLaplaceShape shape

    def __cinit__(self, double bond):
        self.shape = cYoungLaplaceShape(bond)

    def __call__(self, double s):
        cdef vector2f v = self.shape(s)
        return np.array(<double[:2]> v.data())

    def DBo(self, double s):
        cdef vector2f v = self.shape.DBo(s)
        return np.array(<double[:2]> v.data())

    def z_inv(self, double z):
        return self.shape.z_inv(z)

    def closest(self, double r, double z):
        return self.shape.closest(r, z)

    def volume(self, double s):
        return self.shape.volume(s)

    def surface_area(self, double s):
        return self.shape.surface_area(s)

    @property
    def bond(self):
        return self.shape.bond
