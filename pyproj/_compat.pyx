from pyproj.compat import pystrdecode


cdef cstrdecode(const char *instring):
    if instring != NULL:
        return pystrdecode(instring)
    return None
