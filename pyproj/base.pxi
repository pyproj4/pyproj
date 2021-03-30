from cpython.ref cimport PyObject
from cpython.mem cimport PyMem_Malloc, PyMem_Free

cimport cython

from math import radians, degrees


cdef double _DG2RAD = radians(1.)
cdef double _RAD2DG = degrees(1.)
cdef int _DOUBLESIZE = sizeof(double)


cdef extern from "math.h":
    ctypedef enum:
        HUGE_VAL


cdef extern from "Python.h":
    ctypedef enum:
        PyBUF_WRITABLE
    int PyObject_GetBuffer(PyObject *exporter, Py_buffer *view, int flags)
    void PyBuffer_Release(Py_buffer *view)


cdef class PyBuffWriteManager:
    cdef Py_buffer buffer
    cdef double* data
    cdef public Py_ssize_t len

    def __cinit__(self):
        self.data = NULL

    def __init__(self, object data):
        if PyObject_GetBuffer(<PyObject *>data, &self.buffer, PyBUF_WRITABLE) <> 0:
            raise BufferError("pyproj had a problem getting the buffer from data.")
        self.data = <double *>self.buffer.buf
        self.len = self.buffer.len // self.buffer.itemsize

    def __dealloc__(self):
        PyBuffer_Release(&self.buffer)
        self.data = NULL


cdef class PySimpleArray:
    cdef double* data
    cdef public Py_ssize_t len

    def __cinit__(self):
        self.data = NULL

    def __init__(self, Py_ssize_t arr_len):
        self.len = arr_len
        self.data = <double*> PyMem_Malloc(arr_len * sizeof(double))
        if self.data == NULL:
            raise MemoryError("error creating array for pyproj")

    def __dealloc__(self):
        PyMem_Free(self.data)
        self.data = NULL

    @cython.boundscheck(False)
    @cython.wraparound(False)
    cdef double min(self) nogil:
        cdef int iii = 0
        cdef double min_value = self.data[0]
        for iii in range(1, self.len):
            if self.data[iii] < min_value:
                min_value = self.data[iii]
        return min_value

    @cython.boundscheck(False)
    @cython.wraparound(False)
    cdef double max(self) nogil:
        cdef int iii = 0
        cdef double max_value = self.data[0]
        for iii in range(1, self.len):
            if (self.data[iii] > max_value or
                (max_value == HUGE_VAL and self.data[iii] != HUGE_VAL)
            ):
                max_value = self.data[iii]
        return max_value
