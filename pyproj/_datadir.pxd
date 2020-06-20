include "proj.pxi"

cdef void pyproj_context_initialize(
    PJ_CONTEXT* context,
    bint free_context_on_error,
    network=*) except *
