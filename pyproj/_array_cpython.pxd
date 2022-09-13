"""
cpython array utilities

https://github.com/pyproj4/pyproj/issues/854
"""
from cpython cimport array


cdef array.array empty_array(int npts)
