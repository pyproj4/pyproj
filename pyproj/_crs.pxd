include "proj.pxi"

cdef class Axis:
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


cdef class Base:
    cdef PJ *projobj
    cdef PJ_CONTEXT *projctx
    cdef public object name


cdef class Ellipsoid(Base):
    cdef double _semi_major_metre
    cdef double _semi_minor_metre
    cdef public object is_semi_minor_computed
    cdef double _inv_flattening
    cdef public object ellipsoid_loaded

    @staticmethod
    cdef create(PJ* ellipsoid_pj)

cdef class PrimeMeridian(Base):
    cdef public double longitude
    cdef public double unit_conversion_factor
    cdef public object unit_name

    @staticmethod
    cdef create(PJ* prime_meridian_pj)


cdef class Datum(Base):
    cdef public object _ellipsoid
    cdef public object _prime_meridian

    @staticmethod
    cdef create(PJ* datum_pj)


cdef class CoordinateSystem(Base):
    cdef public object _axis_list

    @staticmethod
    cdef create(PJ* coordinate_system_pj)


cdef class Param:
    cdef public object name
    cdef public object auth_name
    cdef public object code
    cdef public object value
    cdef public double unit_conversion_factor
    cdef public object unit_name
    cdef public object unit_auth_name
    cdef public object unit_code
    cdef public object unit_category

    @staticmethod
    cdef create(PJ_CONTEXT* projcontext, PJ* projobj, int param_idx)


cdef class Grid:
    cdef public object short_name
    cdef public object full_name
    cdef public object package_name
    cdef public object url
    cdef public object direct_download
    cdef public object open_license
    cdef public object available

    @staticmethod
    cdef create(PJ_CONTEXT* projcontext, PJ* projobj, int grid_idx)


cdef class CoordinateOperation(Base):
    cdef public object _params
    cdef public object _grids
    cdef public object method_name
    cdef public object method_auth_name
    cdef public object method_code
    cdef public double accuracy
    cdef public object is_instantiable
    cdef public object has_ballpark_transformation
    cdef public object _towgs84

    @staticmethod
    cdef create(PJ* coordinate_operation_pj)


cdef class _CRS(Base):
    cdef PJ_TYPE _type
    cdef PJ_PROJ_INFO projpj_info
    cdef char *pjinitstring
    cdef public object srs
    cdef public object type_name
    cdef object _ellipsoid
    cdef object _area_of_use
    cdef object _prime_meridian
    cdef object _datum
    cdef object _sub_crs_list
    cdef object _source_crs
    cdef object _target_crs
    cdef object _geodetic_crs
    cdef object _coordinate_system
    cdef object _coordinate_operation