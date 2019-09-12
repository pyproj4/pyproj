import math

cdef double _DG2RAD = math.radians(1.)
cdef double _RAD2DG = math.degrees(1.)
cdef int _DOUBLESIZE = sizeof(double)

cdef extern from "math.h":
    cdef enum:
        HUGE_VAL
        FP_NAN

cdef extern from "Python.h":
    int PyObject_AsWriteBuffer(object, void **rbuf, Py_ssize_t *len)


