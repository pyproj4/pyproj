include "proj.pxi"

from pyproj._datadir cimport ContextManager

cdef class Axis:
    cdef readonly object name
    cdef readonly object abbrev
    cdef readonly object direction
    cdef readonly double unit_conversion_factor
    cdef readonly object unit_name
    cdef readonly object unit_auth_code
    cdef readonly object unit_code

    @staticmethod
    cdef create(ContextManager context_manager, PJ* projobj, int index)

cdef class AreaOfUse:
    cdef readonly double west
    cdef readonly double south
    cdef readonly double east
    cdef readonly double north
    cdef readonly object name

    @staticmethod
    cdef create(ContextManager context_manager, PJ* projobj)


cdef class Base:
    cdef PJ *projobj
    cdef ContextManager context_manager
    cdef readonly object name


cdef class Ellipsoid(Base):
    cdef double _semi_major_metre
    cdef double _semi_minor_metre
    cdef readonly object is_semi_minor_computed
    cdef double _inv_flattening
    cdef readonly object ellipsoid_loaded

    @staticmethod
    cdef create(ContextManager context_manager, PJ* ellipsoid_pj)

cdef class PrimeMeridian(Base):
    cdef readonly double longitude
    cdef readonly double unit_conversion_factor
    cdef readonly object unit_name

    @staticmethod
    cdef create(ContextManager context_manager, PJ* prime_meridian_pj)


cdef class Datum(Base):
    cdef readonly object _ellipsoid
    cdef readonly object _prime_meridian

    @staticmethod
    cdef create(ContextManager context_manager, PJ* datum_pj)


cdef class CoordinateSystem(Base):
    cdef readonly object _axis_list

    @staticmethod
    cdef create(ContextManager context_manager, PJ* coordinate_system_pj)


cdef class Param:
    cdef readonly object name
    cdef readonly object auth_name
    cdef readonly object code
    cdef readonly object value
    cdef readonly double unit_conversion_factor
    cdef readonly object unit_name
    cdef readonly object unit_auth_name
    cdef readonly object unit_code
    cdef readonly object unit_category

    @staticmethod
    cdef create(ContextManager context_manager, PJ* projobj, int param_idx)


cdef class Grid:
    cdef readonly object short_name
    cdef readonly object full_name
    cdef readonly object package_name
    cdef readonly object url
    cdef readonly object direct_download
    cdef readonly object open_license
    cdef readonly object available

    @staticmethod
    cdef create(ContextManager context_manager, PJ* projobj, int grid_idx)


cdef class CoordinateOperation(Base):
    cdef readonly object _params
    cdef readonly object _grids
    cdef readonly object _area_of_use
    cdef readonly object method_name
    cdef readonly object method_auth_name
    cdef readonly object method_code
    cdef readonly double accuracy
    cdef readonly object is_instantiable
    cdef readonly object has_ballpark_transformation
    cdef readonly object _towgs84

    @staticmethod
    cdef create(ContextManager context_manager, PJ* coordinate_operation_pj)


cdef class _CRS(Base):
    cdef PJ_TYPE _type
    cdef PJ_PROJ_INFO projpj_info
    cdef readonly object srs
    cdef readonly object type_name
    cdef readonly object _ellipsoid
    cdef readonly object _area_of_use
    cdef readonly object _prime_meridian
    cdef readonly object _datum
    cdef readonly object _sub_crs_list
    cdef readonly object _source_crs
    cdef readonly object _target_crs
    cdef readonly object _geodetic_crs
    cdef readonly object _coordinate_system
    cdef readonly object _coordinate_operation
