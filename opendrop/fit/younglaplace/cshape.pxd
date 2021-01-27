cdef extern from "<array>" namespace "std" nogil:
    cdef cppclass vector2f "std::array<double, 2>":
        vector2f() except+
        double & operator[](size_t)
        double * data()


cdef extern from "opendrop/younglaplace.hpp" namespace "opendrop::younglaplace":
    cdef cppclass YoungLaplaceShape "opendrop::younglaplace::YoungLaplaceShape<double>":
        double bond

        YoungLaplaceShape() except+
        YoungLaplaceShape(double bond) except+
        vector2f operator()(double s) except+
        vector2f DBo(double s) except+
        double z_inv(double z) except+
        double closest(double r, double z)
        double volume(double s) except+
        double surface_area(double s) except+
