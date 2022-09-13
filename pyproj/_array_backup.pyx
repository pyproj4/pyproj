"""
non-cpython array utilities

https://github.com/pyproj4/pyproj/issues/854
"""
cdef empty_array(int npts):
    return array.array("d", [float("NaN")] * npts)
