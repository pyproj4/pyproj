include "proj.pxi"

from pyproj._crs cimport Base, _CRS, CoordinateOperation


cdef class _Transformer(Base):
    cdef PJ_PROJ_INFO proj_info
    cdef readonly input_geographic
    cdef readonly output_geographic
    cdef object _input_radians
    cdef object _output_radians
    cdef readonly is_pipeline
    cdef readonly skip_equivalent
    cdef readonly projections_equivalent
    cdef readonly projections_exact_same
    cdef readonly type_name  

    @staticmethod
    cdef _Transformer _from_pj(
        PJ *transform_pj,
        _CRS crs_from,
        _CRS crs_to,
        skip_equivalent,
        always_xy
    )