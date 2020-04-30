include "proj.pxi"

from collections import namedtuple
from enum import IntEnum
import warnings

from pyproj.compat import cstrencode, pystrdecode
from pyproj.enums import PJType
from pyproj._datadir cimport pyproj_context_initialize


def get_proj_operations_map():
    """
    Returns
    -------
    dict:
        Operations supported by PROJ.
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
    dict:
        Ellipsoids supported by PROJ.
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
    dict:
        Prime Meridians supported by PROJ.
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
    dict:
        Units supported by PROJ
    """
    warnings.warn(
        "The behavior of 'pyproj.get_units_map' is deprecated "
        "and will change in version 3.0.0.",
        DeprecationWarning,
        stacklevel=2,
    )
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
    dict:
        Angular units supported by PROJ
    """
    warnings.warn(
        "'pyproj.get_angular_units_map' is deprecated. "
        "Angular units will be available "
        "in 'pyproj.get_units_map' in version 3.0.0.",
        DeprecationWarning,
        stacklevel=2,
    )
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
    List[str]:
        Authorities in PROJ database.
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


PJ_TYPE_MAP = {
    PJType.UNKNOWN: PJ_TYPE_UNKNOWN,
    PJType.ELLIPSOID: PJ_TYPE_ELLIPSOID,
    PJType.PRIME_MERIDIAN: PJ_TYPE_PRIME_MERIDIAN,
    PJType.GEODETIC_REFERENCE_FRAME: PJ_TYPE_GEODETIC_REFERENCE_FRAME,
    PJType.DYNAMIC_GEODETIC_REFERENCE_FRAME: PJ_TYPE_DYNAMIC_GEODETIC_REFERENCE_FRAME,
    PJType.VERTICAL_REFERENCE_FRAME: PJ_TYPE_VERTICAL_REFERENCE_FRAME,
    PJType.DYNAMIC_VERTICAL_REFERENCE_FRAME: PJ_TYPE_DYNAMIC_VERTICAL_REFERENCE_FRAME,
    PJType.DATUM_ENSEMBLE: PJ_TYPE_DATUM_ENSEMBLE,
    PJType.CRS: PJ_TYPE_CRS,
    PJType.GEODETIC_CRS: PJ_TYPE_GEODETIC_CRS,
    PJType.GEOCENTRIC_CRS: PJ_TYPE_GEOCENTRIC_CRS,
    PJType.GEOGRAPHIC_CRS: PJ_TYPE_GEOGRAPHIC_CRS,
    PJType.GEOGRAPHIC_2D_CRS: PJ_TYPE_GEOGRAPHIC_2D_CRS,
    PJType.GEOGRAPHIC_3D_CRS: PJ_TYPE_GEOGRAPHIC_3D_CRS,
    PJType.VERTICAL_CRS: PJ_TYPE_VERTICAL_CRS,
    PJType.PROJECTED_CRS: PJ_TYPE_PROJECTED_CRS,
    PJType.COMPOUND_CRS: PJ_TYPE_COMPOUND_CRS,
    PJType.TEMPORAL_CRS: PJ_TYPE_TEMPORAL_CRS,
    PJType.ENGINEERING_CRS: PJ_TYPE_ENGINEERING_CRS,
    PJType.BOUND_CRS: PJ_TYPE_BOUND_CRS,
    PJType.OTHER_CRS: PJ_TYPE_OTHER_CRS,
    PJType.CONVERSION: PJ_TYPE_CONVERSION,
    PJType.TRANSFORMATION: PJ_TYPE_TRANSFORMATION,
    PJType.CONCATENATED_OPERATION: PJ_TYPE_CONCATENATED_OPERATION,
    PJType.OTHER_COORDINATE_OPERATION: PJ_TYPE_OTHER_COORDINATE_OPERATION,
}


def get_codes(auth_name, pj_type, allow_deprecated=False):
    """
    .. versionadded:: 2.4.0

    Parameters
    ----------
    auth_name: str
        The name of the authority.
    pj_type: pyproj.enums.PJType
        The type of object to get the authorities.
    allow_deprecated: bool, optional
        Allow a deprecated code in the return.

    Returns
    -------
    List[str]:
        Codes associated with authorities in PROJ database.
    """
    cdef PJ_CONTEXT* context = NULL
    cdef PJ_TYPE cpj_type = PJ_TYPE_MAP[PJType.create(pj_type)]
    cdef PROJ_STRING_LIST proj_code_list = NULL
    try:
        context = proj_context_create()
        pyproj_context_initialize(context, False)
        cpj_type = PJ_TYPE_MAP[PJType.create(pj_type)]
        proj_code_list = proj_get_codes_from_database(
            context,
            cstrencode(auth_name),
            cpj_type,
            allow_deprecated,
        )
    finally:
        proj_context_destroy(context)
    if proj_code_list == NULL:
        return []
    cdef int iii = 0
    try:
        code_list = []
        while proj_code_list[iii] != NULL:
            code_list.append(pystrdecode(proj_code_list[iii]))
            iii += 1
    finally:
        proj_string_list_destroy(proj_code_list)
    return code_list
