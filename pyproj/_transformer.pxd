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
    cdef readonly skip_equivalent
    cdef readonly projections_equivalent
    cdef readonly projections_exact_same
    cdef readonly type_name
    cdef readonly object _operations

    @staticmethod
    cdef _Transformer _from_pj(
        PJ_CONTEXT* context,
        PJ *transform_pj,
        _CRS crs_from,
        _CRS crs_to,
        skip_equivalent,
        always_xy,
    )
