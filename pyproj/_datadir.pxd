include "proj.pxi"

cpdef str _get_proj_error()
cpdef void _clear_proj_error()
cdef PJ_CONTEXT* PYPROJ_GLOBAL_CONTEXT
cdef PJ_CONTEXT* pyproj_context_create() except *
cdef void pyproj_context_destroy(PJ_CONTEXT* context) except *
