include "proj.pxi"

cdef class Proj:
    cdef PJ * projpj
    cdef PJ_PROJ_INFO projpj_info
    cdef readonly srs
