include "proj.pxi"

cdef class _Proj:
    cdef PJ * projobj
    cdef PJ_CONTEXT* context
    cdef PJ_PROJ_INFO projobj_info
    cdef readonly srs
