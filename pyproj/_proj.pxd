include "proj.pxi"

cdef class Proj:
    cdef PJ * projpj
    cdef PJ_CONTEXT * projctx
    cdef PJ_PROJ_INFO projpj_info
    cdef char *pjinitstring
    cdef public object proj_version

cdef class TransProj:
    cdef PJ * projpj
    cdef PJ_CONTEXT * projctx
    cdef public object error_str
