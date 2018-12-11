include "proj.pxi"

cdef class AxisInfo:
    cdef public object name
    cdef public object abbrev
    cdef public object direction
    cdef public double unit_conversion_factor
    cdef public object unit_name
    cdef public object unit_auth_code
    cdef public object unit_code

    @staticmethod
    cdef create(PJ_CONTEXT* projcontext, PJ* projobj, int index)

cdef class AreaOfUse:
    cdef public double west
    cdef public double south
    cdef public double east
    cdef public double north
    cdef public object name

    @staticmethod
    cdef create(PJ_CONTEXT* projcontext, PJ* projobj)

cdef class Ellipsoid:
    cdef double _semi_major_metre
    cdef double _semi_minor_metre
    cdef public int is_semi_minor_computed
    cdef double _inv_flattening
    cdef public int ellipsoid_loaded

    @staticmethod
    cdef create(PJ_CONTEXT* projcontext, PJ* projobj)

cdef class PrimeMeridian:
    cdef public double longitude
    cdef public double unit_conversion_factor
    cdef public object unit_name

    @staticmethod
    cdef create(PJ_CONTEXT* projcontext, PJ* projobj)


cdef class _CRS:
    cdef PJ * projobj
    cdef PJ_CONTEXT * projctx
    cdef PJ_TYPE proj_type
    cdef PJ_PROJ_INFO projpj_info
    cdef public object proj_version
    cdef char *pjinitstring
    cdef public object name
    cdef public object srs
    cdef public object _ellipsoid
    cdef public object _area_of_use
    cdef public object _prime_meridian
    cdef public object _axis_info
