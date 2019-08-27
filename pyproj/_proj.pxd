include "proj.pxi"

from pyproj._datadir cimport ContextManager

cdef class Proj:
    cdef PJ * projobj
    cdef PJ_PROJ_INFO projobj_info
    cdef ContextManager context_manager
    cdef readonly srs
