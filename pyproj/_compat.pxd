cdef str cstrdecode(const char *instring)
cpdef bytes cstrencode(str pystr)


cdef inline bint _is_scalar(object value):
    """
    Check whether ``value`` is a single number that the point-optimized
    functions can consume.

    This must be called *before* any implicit ``double x = value`` conversion.
    """
    if isinstance(value, (float, int)):
        return True
    return getattr(value, "ndim", -1) == 0


IF CTE_PYTHON_IMPLEMENTATION == "CPython":
    from cpython cimport array
    cdef array.array empty_array(int npts)

ELSE:
    # https://github.com/pyproj4/pyproj/issues/854
    cdef empty_array(int npts)
