include "proj.pxi"

cdef class _Transformer:
    cdef PJ * projpj
    cdef PJ_CONTEXT * projctx
    cdef public object from_geographic
    cdef public object to_geographic