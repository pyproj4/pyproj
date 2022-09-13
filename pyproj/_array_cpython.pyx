"""
cpython array utilities

https://github.com/pyproj4/pyproj/issues/854
"""

from cpython cimport array


cdef array.array _ARRAY_TEMPLATE = array.array("d", [])

cdef array.array empty_array(int npts):
    return array.clone(_ARRAY_TEMPLATE, npts, zero=False)
