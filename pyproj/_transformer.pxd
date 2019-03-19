include "proj.pxi"

cdef class _Transformer:
    cdef PJ * projpj
    cdef PJ_CONTEXT * projctx
    cdef public object input_geographic
    cdef public object output_geographic
    cdef public object input_radians
    cdef public object output_radians
    cdef public object is_pipeline
    cdef public object skip_equivalent
    cdef public object projections_equivalent
    cdef public object projections_exact_same
    
