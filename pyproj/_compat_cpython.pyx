import array


cpdef bytes cstrencode(str pystr):
    """
    Encode a string into bytes.
    """
    try:
        return pystr.encode("utf-8")
    except UnicodeDecodeError:
        return pystr.decode("utf-8").encode("utf-8")


cdef str cstrdecode(const char *instring):
    if instring != NULL:
        return instring
    return None


from cpython cimport array

cdef array.array _ARRAY_TEMPLATE = array.array("d", [])

cdef array.array empty_array(int npts):
    return array.clone(_ARRAY_TEMPLATE, npts, zero=False)
