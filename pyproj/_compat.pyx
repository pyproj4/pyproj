import array

from pyproj.compat import pystrdecode


cdef cstrdecode(const char *instring):
    if instring != NULL:
        return pystrdecode(instring)
    return None


IF CTE_PYTHON_IMPLEMENTATION == "CPython":
    from cpython cimport array

    cdef array.array _ARRAY_TEMPLATE = array.array("d", [])

    def empty_array(int npts):
        return array.clone(_ARRAY_TEMPLATE, npts, zero=False)

ELSE:
    # https://github.com/pyproj4/pyproj/issues/854
    def empty_array(int npts):
        return array.array("d", [float("NaN")] * npts)
