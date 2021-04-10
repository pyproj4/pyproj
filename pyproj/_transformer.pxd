include "proj.pxi"

from pyproj._crs cimport _CRS, Base


cdef class _TransformerGroup:
    cdef PJ_CONTEXT* context
    cdef readonly _transformers
    cdef readonly _unavailable_operations
    cdef readonly _best_available

cdef class _Transformer(Base):
    cdef PJ_PROJ_INFO proj_info
    cdef readonly _area_of_use
    cdef readonly type_name
    cdef readonly object _operations

    @staticmethod
    cdef _Transformer _from_pj(
        PJ_CONTEXT* context,
        PJ *transform_pj,
        always_xy,
    )
