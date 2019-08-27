include "proj.pxi"

cdef class ContextManager:
    cdef PJ_CONTEXT *context
    cdef object _set_search_paths