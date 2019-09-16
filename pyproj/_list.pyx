include "proj.pxi"

from collections import namedtuple
from enum import IntEnum

from pyproj.compat import cstrencode, pystrdecode
from pyproj._datadir cimport pyproj_context_initialize

def get_proj_operations_map():
    """
    Returns
    -------
    dict: operations supported by PROJ.
    """
    cdef PJ_OPERATIONS *proj_operations = proj_list_operations()
    cdef int iii = 0
    operations_map = {}
    while proj_operations[iii].id != NULL:
        operations_map[pystrdecode(proj_operations[iii].id)] = \
            pystrdecode(proj_operations[iii].descr[0]).split("\n\t")[0]
        iii += 1
    return operations_map


def get_ellps_map():
    """
    Returns
    -------
    dict: ellipsoids supported by PROJ.
    """
    cdef PJ_ELLPS *proj_ellps = proj_list_ellps()
    cdef int iii = 0
    ellps_map = {}
    while proj_ellps[iii].id != NULL:
        major_key, major_val = pystrdecode(proj_ellps[iii].major).split("=")
        ell_key, ell_val = pystrdecode(proj_ellps[iii].ell).split("=")
        ellps_map[pystrdecode(proj_ellps[iii].id)] = {
            major_key: float(major_val),
            ell_key: float(ell_val),
            "description": pystrdecode(proj_ellps[iii].name)
        }
        iii += 1
    return ellps_map


def get_prime_meridians_map():
    """
    Returns
    -------
    dict: prime meridians supported by PROJ.
    """
    cdef PJ_PRIME_MERIDIANS *prime_meridians = proj_list_prime_meridians()
    cdef int iii = 0
    prime_meridians_map = {}
    while prime_meridians[iii].id != NULL:
        prime_meridians_map[pystrdecode(prime_meridians[iii].id)] = \
            pystrdecode(prime_meridians[iii].defn)
        iii += 1
    return prime_meridians_map


Unit = namedtuple("Unit", ["id", "to_meter", "name", "factor"])


def get_units_map():
    """
    Returns
    -------
    dict: units supported by PROJ
    """
    cdef PJ_UNITS *proj_units = proj_list_units()
    cdef int iii = 0
    units_map = {}
    while proj_units[iii].id != NULL:
        units_map[pystrdecode(proj_units[iii].id)] = Unit(
            id=pystrdecode(proj_units[iii].id),
            to_meter=pystrdecode(proj_units[iii].to_meter),
            name=pystrdecode(proj_units[iii].name),
            factor=proj_units[iii].factor,
        )
        iii += 1
    return units_map


def get_angular_units_map():
    """
    Returns
    -------
    dict: angular units supported by PROJ
    """
    cdef PJ_UNITS *proj_units = proj_list_angular_units()
    cdef int iii = 0
    units_map = {}
    while proj_units[iii].id != NULL:
        units_map[pystrdecode(proj_units[iii].id)] = Unit(
            id=pystrdecode(proj_units[iii].id),
            to_meter=pystrdecode(proj_units[iii].to_meter),
            name=pystrdecode(proj_units[iii].name),
            factor=proj_units[iii].factor,
        )
        iii += 1
    return units_map


def get_authorities():
    """
    .. versionadded:: 2.4.0

    Returns
    -------
    list[str]: Authorities in PROJ database.
    """
    cdef PJ_CONTEXT* context = proj_context_create()
    pyproj_context_initialize(context, True)
    cdef PROJ_STRING_LIST proj_auth_list = proj_get_authorities_from_database(context)
    if proj_auth_list == NULL:
        proj_context_destroy(context)
        return []
    cdef int iii = 0
    try:
        auth_list = []
        while proj_auth_list[iii] != NULL:
            auth_list.append(pystrdecode(proj_auth_list[iii]))
            iii += 1
    finally:
        proj_context_destroy(context)
        proj_string_list_destroy(proj_auth_list)
    return auth_list


class PJTypes(IntEnum):
    """
    .. versionadded:: 2.4.0

    PJ Types for listing codes with :func:`~pyproj.get_codes`

    Attributes
    ----------
    UNKNOWN
    ELLIPSOID
    PRIME_MERIDIAN
    GEODETIC_REFERENCE_FRAME
    DYNAMIC_GEODETIC_REFERENCE_FRAME
    VERTICAL_REFERENCE_FRAME
    DYNAMIC_VERTICAL_REFERENCE_FRAME
    DATUM_ENSEMBLE
    CRS
    GEODETIC_CRS
    GEOCENTRIC_CRS
    GEOGRAPHIC_CRS
    GEOGRAPHIC_2D_CRS
    GEOGRAPHIC_3D_CRS
    VERTICAL_CRS
    PROJECTED_CRS
    COMPOUND_CRS
    TEMPORAL_CRS
    ENGINEERING_CRS
    BOUND_CRS
    OTHER_CRS
    CONVERSION
    TRANSFORMATION
    CONCATENATED_OPERATION
    OTHER_COORDINATE_OPERATION

    """
    UNKNOWN = PJ_TYPE_UNKNOWN
    ELLIPSOID = PJ_TYPE_ELLIPSOID
    PRIME_MERIDIAN = PJ_TYPE_PRIME_MERIDIAN
    GEODETIC_REFERENCE_FRAME = PJ_TYPE_GEODETIC_REFERENCE_FRAME
    DYNAMIC_GEODETIC_REFERENCE_FRAME = PJ_TYPE_DYNAMIC_GEODETIC_REFERENCE_FRAME
    VERTICAL_REFERENCE_FRAME = PJ_TYPE_VERTICAL_REFERENCE_FRAME
    DYNAMIC_VERTICAL_REFERENCE_FRAME = PJ_TYPE_DYNAMIC_VERTICAL_REFERENCE_FRAME
    DATUM_ENSEMBLE = PJ_TYPE_DATUM_ENSEMBLE
    CRS = PJ_TYPE_CRS
    GEODETIC_CRS = PJ_TYPE_GEODETIC_CRS
    GEOCENTRIC_CRS = PJ_TYPE_GEOCENTRIC_CRS
    GEOGRAPHIC_CRS = PJ_TYPE_GEOGRAPHIC_CRS
    GEOGRAPHIC_2D_CRS = PJ_TYPE_GEOGRAPHIC_2D_CRS
    GEOGRAPHIC_3D_CRS = PJ_TYPE_GEOGRAPHIC_3D_CRS
    VERTICAL_CRS = PJ_TYPE_VERTICAL_CRS
    PROJECTED_CRS = PJ_TYPE_PROJECTED_CRS
    COMPOUND_CRS = PJ_TYPE_COMPOUND_CRS
    TEMPORAL_CRS = PJ_TYPE_TEMPORAL_CRS
    ENGINEERING_CRS = PJ_TYPE_ENGINEERING_CRS
    BOUND_CRS = PJ_TYPE_BOUND_CRS
    OTHER_CRS = PJ_TYPE_OTHER_CRS
    CONVERSION = PJ_TYPE_CONVERSION
    TRANSFORMATION = PJ_TYPE_TRANSFORMATION
    CONCATENATED_OPERATION = PJ_TYPE_CONCATENATED_OPERATION
    OTHER_COORDINATE_OPERATION = PJ_TYPE_OTHER_COORDINATE_OPERATION


def get_codes(auth_name, pj_type, allow_deprecated=False):
    """
    .. versionadded:: 2.4.0

    Parameters
    ----------
    auth_name: str
        The name of the authority.
    pj_type: ~pyproj.enums.PJTypes
        The type of object to get the authorities.
    allow_deprecated: bool, optional
        Allow a deprecated code in the return.

    Returns
    -------
    list[str]: Codes associated with authorities in PROJ database.
    """
    cdef PJ_CONTEXT* context = proj_context_create()
    pyproj_context_initialize(context, True)
    cdef PROJ_STRING_LIST proj_code_list = proj_get_codes_from_database(
        context,
        cstrencode(auth_name),
        <PJ_TYPE>pj_type,
        allow_deprecated,
    )
    if proj_code_list == NULL:
        proj_context_destroy(context)
        return []
    cdef int iii = 0
    try:
        code_list = []
        while proj_code_list[iii] != NULL:
            code_list.append(pystrdecode(proj_code_list[iii]))
            iii += 1
    finally:
        proj_context_destroy(context)
        proj_string_list_destroy(proj_code_list)
    return code_list
