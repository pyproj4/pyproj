include "proj.pxi"

cdef ContextManager PROJ_CONTEXT

cdef class ContextManager:
    cdef PJ_CONTEXT *context
